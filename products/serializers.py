from rest_framework import serializers
from .models import Category, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image']



class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'price',
            'image',
            'available',
            'created_at',
            'category',
            'category_id',
            'is_new',
            'is_featured'
        ]

class ProductInventorySerializer(serializers.ModelSerializer):
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'quantity', 'stock_status']

    def get_stock_status(self, obj):
        LOW_STOCK_THRESHOLD = 5  # Customize as needed

        if obj.quantity == 0:
            return 'Out of Stock'
        elif obj.quantity <= LOW_STOCK_THRESHOLD:
            return 'Low Stock'
        else:
            return 'In Stock'



class ProductVariantSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'product','product_details', 'color', 'size', 'quantity']