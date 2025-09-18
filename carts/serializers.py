# serializers.py (separate file)
from rest_framework import serializers
from .models import Cart, CartItem
from products.models import ProductVariant
from products.serializers import ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    variant_details = ProductVariantSerializer(source='variant', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'variant', 'variant_details', 'quantity', 'total_price']
        read_only_fields = ['cart', 'added_at']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'session_key', 'created_at', 'updated_at', 'items', 'total', 'total_items']
        
class AddToCartSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    
    def validate(self, data):
        variant_id = data['variant_id']
        quantity = data['quantity']
        
        try:
            variant = ProductVariant.objects.get(id=variant_id)
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError("Product variant does not exist")
        
        if variant.quantity < quantity:
            raise serializers.ValidationError(f"Only {variant.quantity} items available in stock")
        
        data['variant'] = variant
        return data

class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity','variant','id']
    
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value 