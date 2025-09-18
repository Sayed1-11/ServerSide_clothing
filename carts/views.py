# views.py
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer,UpdateCartItemSerializer,AddToCartSerializer
from products.models import ProductVariant
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

class CartViewSet(viewsets.GenericViewSet, 
                 mixins.RetrieveModelMixin,
                 mixins.ListModelMixin):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['session_key']
    def get_queryset(self):
        session_key = self.request.query_params.get('session_key')
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return Cart.objects.filter(session_key=session_key)
    
    def get_object(self):
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        try:
            cart = Cart.objects.get(pk=pk)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

        add_serializer = AddToCartSerializer(data=request.data)

        if add_serializer.is_valid():
            variant = add_serializer.validated_data['variant']
            quantity = add_serializer.validated_data['quantity']

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                variant=variant,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(add_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        try:
            cart = Cart.objects.get(id=pk)  # ← Get cart by ID from URL
            items = cart.items.all()
            serializer = CartItemSerializer(items, many=True)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

class CartItemViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin
):
    permission_classes = [AllowAny]
    serializer_class = UpdateCartItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cart']
    
    def get_queryset(self):
        session_key = self.request.query_params.get('session_key') # This is None for /36/
        if not session_key:
            return CartItem.objects.none() 
        
        try:
            cart = Cart.objects.get(session_key=session_key)
            return CartItem.objects.filter(cart=cart)
        except Cart.DoesNotExist:
            return CartItem.objects.none()
    
    def update(self, request, *args, **kwargs):
        cart_item = self.get_object()
        serializer = self.get_serializer(cart_item, data=request.data)
    
        if serializer.is_valid():
            new_quantity = serializer.validated_data['quantity']
            
            # Use product quantity instead of variant quantity
            max_available = cart_item.variant.product.quantity
            
            print(f"Requested: {new_quantity}, Available: {max_available}")  # Debug
            
            if new_quantity > max_available:
                return Response(
                    {"error": f"Only {max_available} items available"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def destroy(self, request, *args, **kwargs):
        """Clear a specific cart item"""
        try:
            cart_item = self.get_object()
            cart_item.delete()
            return Response(
                {"message": "Item removed from cart successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        session_key = self.request.query_params.get('session_key')
        if not session_key:
            return Response(
                {"error": "Session key required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart = Cart.objects.get(session_key=session_key)
            items_count = cart.items.count()
            cart.items.all().delete()
            
            return Response({
                "message": f"Cleared {items_count} items from cart",
                "cart_id": cart.id
            }, status=status.HTTP_200_OK)
            
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)