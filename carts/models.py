# models.py
from django.db import models
from products.models import ProductVariant
from django.forms import ValidationError
from django.utils import timezone
from datetime import timedelta

class CartManager(models.Manager):
    def get_or_create_with_cleanup(self, session_key):
        import random
        if random.randint(1, 100) == 1:
            self.cleanup_old_empty_carts()
        
        return self.get_or_create(session_key=session_key)
    
    def cleanup_old_empty_carts(self):
        """Delete empty carts older than 1 day"""
        one_day_ago = timezone.now() - timedelta(days=1)
        
        empty_carts = self.filter(
            items__isnull=True,
            updated_at__lt=one_day_ago
        )
        
        count = empty_carts.count()
        if count > 0:
            empty_carts.delete()
            print(f"Cleaned up {count} empty carts")
        return count

class Cart(models.Model):
    session_key = models.CharField(max_length=40, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    objects = CartManager()

    def __str__(self):
        return f"Cart (Session: {self.session_key})"

    @property
    def total(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def is_empty(self):
        return self.items.count() == 0
    
    def should_be_deleted(self):
        """Check if cart should be deleted (empty and older than 1 day)"""
        if not self.is_empty:
            return False
        
        one_day_ago = timezone.now() - timedelta(days=1)
        return self.updated_at < one_day_ago
    
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