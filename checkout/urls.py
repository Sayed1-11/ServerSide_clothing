from .views import OrderViewSet,SalesAnalyticsView
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views
router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
urlpatterns = [
    path('', include(router.urls)),
    path('sales/daily/', SalesAnalyticsView.as_view(), name='sales'),
    path('payment/success/', views.ssl_payment_success, name='payment-success'),
    path('payment/fail/', views.ssl_payment_fail, name='payment-fail'),
    path('payment/cancel/', views.ssl_payment_cancel, name='payment-cancel'),
]