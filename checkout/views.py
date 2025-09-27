from .models import Order
from .serializers import OrderSerializer,MonthlySalesSerializer,DailySalesSerializer,TotalSalesSerializer
from rest_framework import viewsets,status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import redirect
from django.conf import settings
import uuid
import requests
from rest_framework.decorators import api_view,permission_classes
from django.db import transaction
from rest_framework import serializers

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post', 'delete']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        cart_items = validated_data.pop('cart_items')
        total = sum(item.quantity * item.variant.product.price for item in cart_items)

        if validated_data.get('shipping_method') == 'online_payment':
            with transaction.atomic():
                order = Order.objects.create(
                    **validated_data,
                    total=total,
                )
                order.cart_items.set(cart_items)

            tran_id = f"order_{order.id}_{uuid.uuid4().hex[:8]}"
            order.transaction_id = tran_id
            order.save()

            sslcz_url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
            payload = {
                "store_id": settings.SSLCZ_STORE_ID,
                "store_passwd": settings.SSLCZ_STORE_PASS,
                "total_amount": str(total),
                "currency": "BDT",
                "tran_id": tran_id,
                "success_url": request.build_absolute_uri("/api/checkout/payment/success/"),
                "fail_url": request.build_absolute_uri("/api/checkout/payment/fail/"),
                "cancel_url": request.build_absolute_uri("/api/checkout/payment/cancel/"),
                "cus_name": validated_data.get("full_name"),
                "cus_email": validated_data.get("email") or "example@email.com",
                "cus_add1": validated_data.get("address") or "No address",
                "cus_phone": validated_data.get("phone") or "N/A",
                "cus_city": validated_data.get("city") or "Dhaka",
                "cus_country": "Bangladesh",
                "shipping_method": "NO",
                "product_name": "Order Items",
                "product_category": "General",
                "product_profile": "general",
            }

            try:
                response = requests.post(sslcz_url, data=payload, timeout=10)
                data = response.json()

                if data.get("status") == "SUCCESS":
                    return Response(
                        {
                            "payment_url": data["GatewayPageURL"],
                            "order_id": order.id,
                            "transaction_id": tran_id,
                        },
                        status=status.HTTP_201_CREATED
                    )
                else:
                    order.delete()
                    return Response(
                        {"error": "Failed to initiate SSLCommerz payment", "details": data},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            except requests.exceptions.RequestException as e:
                order.delete()
                return Response(
                    {"error": "SSLCommerz request failed", "details": str(e)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

        # 🟡 Cash on Delivery (COD)
        else:
                # Cash on Delivery
                with transaction.atomic():
                    order = Order.objects.create(
                        **validated_data,
                        total=total,
                    )
                    order.cart_items.set(cart_items)
                    
                    # Update stock
                    for item in cart_items:
                        variant = item.variant
                        product = variant.product
                        
                        if variant.quantity < item.quantity or product.quantity < item.quantity:
                            raise serializers.ValidationError(
                                f"Not enough stock for {product.name}"
                            )
                        
                        variant.quantity -= item.quantity
                        variant.save()
                        
                        product.quantity -= item.quantity
                        product.save()

            # Clear the cart after successful order
            cart = cart_items.first().cart if cart_items.exists() else None
            if cart:
                cart.items.all().delete()

            return Response(
                {
                    "message": "Order created successfully",
                    "order_id": order.id,
                    "total": total
                }, 
                status=status.HTTP_201_CREATED
            )
    

@api_view(['POST'])
@permission_classes([AllowAny]) 
def ssl_payment_success(request):
    tran_id = request.POST.get('tran_id')
    status_val = request.POST.get('status')
    val_id = request.POST.get('val_id')
    
    if status_val != 'VALID':
        return redirect(f"http://localhost:5173/payment/fail?reason=invalid_status&status={status_val}")
    
    try:
        if tran_id and tran_id.startswith("order_"):
            parts = tran_id.split('_')
            if len(parts) >= 2:
                order_id = int(parts[1])
                order = Order.objects.get(id=order_id)
                with transaction.atomic():
                    print("Atomic transaction started")
                    for item in order.cart_items.all():
                        variant = item.variant
                        print("variant", variant)
                        product = variant.product
                        print("Product", product)
                        
                        # Check both variant and product stock
                        if variant.quantity < item.quantity:
                            print(f"Insufficient stock for variant {variant}: {variant.quantity} available, {item.quantity} requested")
                            return redirect(f"http://localhost:5173/payment/fail?reason=insufficient_stock_variant&order_id={order.id}")
                        
                        if product.quantity < item.quantity:
                            print(f"Insufficient stock for product {product}: {product.quantity} available, {item.quantity} requested")
                            return redirect(f"http://localhost:5173/payment/fail?reason=insufficient_stock_product&order_id={order.id}")
                        
                        # Update both variant and product quantities
                        variant.quantity -= item.quantity
                        variant.save()
                        print(f"Variant {variant} quantity updated to {variant.quantity}")
                        
                        product.quantity -= item.quantity
                        product.save()
                        print(f"Product {product} quantity updated to {product.quantity}")
                    
                    print("All items processed, updating order status")
                    order.is_paid = True
                    order.transaction_id = tran_id
                    order.status = 'confirmed'
                    order.save()
                    print(f"Order {order_id} marked as paid")

                return redirect(f"http://localhost:5173/payment/success?order_id={order.id}")
        
        # If not a valid order transaction
        print(f"Invalid transaction ID format: {tran_id}")
        return redirect("http://localhost:5173/payment/fail?reason=invalid_tran_id")

    except (Order.DoesNotExist, ValueError, IndexError) as e:
        print(f"[Payment Success] Error processing order: {e}")
        return redirect(f"http://localhost:5173/payment/fail?reason=order_not_found&tran_id={tran_id}")

    except (Order.DoesNotExist, ValueError, IndexError) as e:
        print(f"[Payment Success] Error processing order: {e}")
        return redirect(f"http://localhost:5173/payment/fail?reason=order_not_found&tran_id={tran_id}")
    
@api_view(['POST'])
@permission_classes([AllowAny]) 
def ssl_payment_fail(request):
    tran_id = request.POST.get('tran_id')
    
    try:
        if tran_id.startswith("order_"):
            parts = tran_id.split('_')
            if len(parts) >= 2:
                order_id = int(parts[1])  
                order = Order.objects.get(id=order_id)
                if not order.is_paid:
                    order.delete()
    except (Order.DoesNotExist, ValueError, IndexError) as e:
        print(f"[Payment Fail] Skipping deletion due to error: {e}")
        pass

    return redirect(f"http://localhost:5173/payment/fail?tran_id={tran_id}")


@api_view(['POST'])
@permission_classes([AllowAny]) 
def ssl_payment_cancel(request):
    tran_id = request.POST.get('tran_id')
    
    try:
        if tran_id.startswith("order_"):
            parts = tran_id.split('_')
            if len(parts) >= 2:
                order_id = int(parts[1])
                order = Order.objects.get(id=order_id)
                if not order.is_paid:
                    order.delete()
    except (Order.DoesNotExist, ValueError, IndexError) as e:
        print(f"[Payment Cancel] Skipping deletion due to error: {e}")
        pass

    return redirect(f"http://localhost:5173/payment/cancel?tran_id={tran_id}")



class SalesAnalyticsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Get parameters with validation
            days = min(max(1, int(request.GET.get('days', 30))), 365)
            months = min(max(1, int(request.GET.get('months', 12))), 36)
            
            # Get today's sales and historical data
            today_sales = DailySalesSerializer.get_today_sales().data
            monthly_data = MonthlySalesSerializer.get_monthly_sales().data
            total_sales = TotalSalesSerializer.get_total_sales().data
            # Convert string values to float for calculations
            def convert_revenue_items(items):
                converted = []
                for item in items:
                    converted_item = item.copy()
                    # Convert DecimalField strings to float
                    if isinstance(converted_item['total_revenue'], str):
                        converted_item['total_revenue'] = float(converted_item['total_revenue'])
                    if isinstance(converted_item['average_order_value'], str):
                        converted_item['average_order_value'] = float(converted_item['average_order_value'])
                    converted.append(converted_item)
                return converted
            
            today_sales_converted = convert_revenue_items(today_sales)
            monthly_data_converted = convert_revenue_items(monthly_data)

            # Calculate summary statistics
            total_today_revenue = sum(item['total_revenue'] for item in today_sales_converted)
            total_today_orders = sum(item['total_orders'] for item in today_sales_converted)
            
            total_monthly_revenue = sum(item['total_revenue'] for item in monthly_data_converted)
            total_monthly_orders = sum(item['total_orders'] for item in monthly_data_converted)
            
            return Response({
                'today_sales': today_sales,
                'monthly_sales': monthly_data,
                'total_sales': total_sales,
                'summary': {
                    'today': {
                        'total_revenue': total_today_revenue,
                        'total_orders': total_today_orders,
                        'average_order_value': total_today_revenue / total_today_orders if total_today_orders > 0 else 0
                    },
                    'monthly': {
                        'total_revenue': total_monthly_revenue,
                        'total_orders': total_monthly_orders,
                        'average_monthly_revenue': total_monthly_revenue / months if months > 0 else 0,
                        'average_monthly_orders': total_monthly_orders / months if months > 0 else 0
                    }
                },
                'parameters': {
                    'days_analyzed': days,
                    'months_analyzed': months
                }
            })
            
        except ValueError:
            return Response({
                'error': 'Invalid parameters. Days and months must be integers.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
