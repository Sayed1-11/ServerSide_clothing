# models.py
from django.db import models
from products.models import ProductVariant
from django.forms import ValidationError

class CartManager(models.Manager):
    def get_or_create_for_session(self, session_key):
        cart, created = self.get_or_create(session_key=session_key)
        return cart
    
    def get_for_session(self, session_key):
        try:
            return self.get(session_key=session_key)
        except Cart.DoesNotExist:
            return None


class Cart(models.Model):
    session_key = models.CharField(max_length=40, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Track last update

    objects = CartManager()

    def __str__(self):
        return f"Cart (Session: {self.session_key})"

    @property
    def total(self):
        return sum(item.total_price for item in self.items.all())
    
    

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['cart', 'variant']

    def __str__(self):
        return f"{self.variant} x {self.quantity}"

    @property
    def total_price(self):
        price = getattr(self.variant, 'price', None) or self.variant.product.price
        return price * self.quantity
    
    def clean(self):
        # Ensure quantity is at least 1
        if self.quantity < 1:
            raise ValidationError("Quantity must be at least 1")