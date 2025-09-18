from rest_framework import viewsets
from .models import Category, Product, ProductVariant
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductVariantSerializer,ProductInventorySerializer
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, SAFE_METHODS,AllowAny
from rest_framework.views import APIView

class ReadOnlyOrAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  
        return request.user and request.user.is_authenticated

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ReadOnlyOrAuthenticated]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [ReadOnlyOrAuthenticated]

class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'color', 'size']
    

class InventoryStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        LOW_STOCK_THRESHOLD = 5

        in_stock = Product.objects.filter(quantity__gt=LOW_STOCK_THRESHOLD).count()
        low_stock = Product.objects.filter(quantity__gt=0, quantity__lte=LOW_STOCK_THRESHOLD).count()
        out_of_stock = Product.objects.filter(quantity=0).count()

        return Response({
            "in_stock": in_stock,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock
        })