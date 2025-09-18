from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import CategoryViewSet, ProductViewSet, ProductVariantViewSet,InventoryStatusView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'variants', ProductVariantViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('inventory/', InventoryStatusView.as_view(), name='inventory-summary'),

]