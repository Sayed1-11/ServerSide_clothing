from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)  # allow blank for auto-fill
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def product_count(self):
        return self.products.count()


class Product(models.Model):
    name = models.CharField(max_length=255)
    categories = models.ManyToManyField(Category, related_name='products')
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    available = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_new = models.BooleanField(default=False)  # For new arrivals
    is_featured = models.BooleanField(default=False)  # For featured products

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.available = self.is_in_stock
        super().save(*args, **kwargs)
    
    def get_primary_category(self):
        """Get the first/main category for breadcrumbs, URLs, etc."""
        return self.categories.first()
    
    @property
    def is_in_stock(self):
        return self.quantity > 0 or any(variant.quantity > 0 for variant in self.variants.all())

        
COLOR_CHOICES = [
    ('red', 'Red'),
    ('blue', 'Blue'),
    ('green', 'Green'),
    ('black', 'Black'),
    ('white', 'White'),
]

SIZE_CHOICES = [
    ('S', 'Small'),
    ('M', 'Medium'),
    ('L', 'Large'),
    ('XL', 'Extra Large'),
]


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    size = models.CharField(max_length=5, choices=SIZE_CHOICES)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.color} / {self.size}"