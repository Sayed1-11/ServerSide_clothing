from .models import Order
from rest_framework import serializers
from .models import Order
from carts.models import CartItem
from django.db.models import Sum, Count
from django.utils import timezone
from django.db.models.functions import ExtractYear, ExtractMonth
from django.db import transaction
from rest_framework import serializers

class OrderSerializer(serializers.ModelSerializer):
    cart_items = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CartItem.objects.all()
    )

    class Meta:
        model = Order
        fields = [
            'id',
            'full_name',
            'address',
            'email',
            'phone',
            'placed_at',
            'cart_items',
            'total',
            'is_paid',
            'shipping_method',
            'city',
        ]
        read_only_fields = ['id', 'placed_at', 'is_paid', 'total']

    def validate_cart_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must have at least one cart item.")
        return value

    def create(self, validated_data):
        try:
            cart_items = validated_data.pop('cart_items')
            with transaction.atomic():  # ✅ Add this
                order = Order.objects.create(**validated_data)
                order.cart_items.set(cart_items)
                total = sum(item.quantity * item.variant.product.price for item in cart_items)
                order.total = total
                order.save()
            
                return order
        except Exception as e:
            print("Error in create():", str(e))
            raise e
        
class DailySalesSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)


    @classmethod
    def get_today_sales(cls):
        """Get sales data for today only"""
        today = timezone.now().date()
        
        # Get today's orders
        today_data = Order.objects.filter(
            placed_at__date=today,
            is_paid=True
        ).aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total')
        )
        
        total_revenue = today_data['total_revenue']
        if isinstance(total_revenue, str):
            total_revenue = float(total_revenue) if total_revenue else 0.0
        elif total_revenue is None:
            total_revenue = 0.0
        
        total_orders = today_data['total_orders'] or 0
        
        result = [{
            'date': today,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'average_order_value': total_revenue / total_orders if total_orders > 0 else 0
        }]
        
        return cls(result, many=True)
class MonthlySalesSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    month_name = serializers.CharField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)

    @classmethod
    def get_monthly_sales(cls):
        monthly_data = Order.objects.filter(
            is_paid=True
        ).annotate(
            year=ExtractYear('placed_at'),
            month=ExtractMonth('placed_at')
        ).values('year', 'month').annotate(
            total_orders=Count('id'),
            total_revenue=Sum('total')
        ).order_by('year', 'month')  # Oldest to newest

        result = []
        for data in monthly_data:
            total_revenue = data['total_revenue'] or 0.0
            total_orders = data['total_orders'] or 0

            average_order_value = (
                total_revenue / total_orders if total_orders > 0 else 0
            )

            result.append({
                'year': int(data['year']),
                'month': int(data['month']),
                'month_name': timezone.datetime(
                    int(data['year']), int(data['month']), 1
                ).strftime('%B'),
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'average_order_value': average_order_value
            })

        return cls(result, many=True)

class TotalSalesSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_items_sold = serializers.IntegerField()
    total_customers = serializers.IntegerField()

    @classmethod
    def get_total_sales(cls):
        """Get overall sales statistics"""
        # Get all paid orders
        paid_orders = Order.objects.filter(is_paid=True)
        
        # Calculate basic metrics
        sales_data = paid_orders.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total'),
            total_customers=Count('email', distinct=True)
        )
        
        # Calculate total items sold by summing quantities from cart_items
        total_items = 0
        for order in paid_orders:
            for cart_item in order.cart_items.all():
                total_items += cart_item.quantity
        
        total_revenue = sales_data['total_revenue']
        if isinstance(total_revenue, str):
            total_revenue = float(total_revenue) if total_revenue else 0.0
        elif total_revenue is None:
            total_revenue = 0.0
        
        total_orders = sales_data['total_orders'] or 0
        total_customers = sales_data['total_customers'] or 0
        
        return cls({
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'average_order_value': total_revenue / total_orders if total_orders > 0 else 0,
            'total_items_sold': total_items,
            'total_customers': total_customers
        })
