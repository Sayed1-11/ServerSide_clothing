from django.db import models
from carts.models import CartItem
SHIPPING_METHOD_CHOICES = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('online_payment', 'Online Payment'),
    ]

class Order(models.Model):
    cart_items = models.ManyToManyField(CartItem, related_name='orders')
    total = models.DecimalField(max_digits=10, decimal_places=2,null=True)  # better for money
    full_name = models.CharField(max_length=255)
    address = models.TextField()
    email = models.EmailField()
    shipping_method = models.CharField(
        max_length=20,
        choices=SHIPPING_METHOD_CHOICES,
        default='cash_on_delivery'
    )
    phone = models.CharField(max_length=20, blank=True)
    placed_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True, blank=True) 
    city = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return f"Order {self.id} for {self.full_name} - {self.get_shipping_method_display()}"

