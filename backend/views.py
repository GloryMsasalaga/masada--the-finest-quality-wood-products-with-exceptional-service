# from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import (Product, Customer, Order, OrderItem, Inventory, InventoryLog, Delivery)
from .serializers import (ProductSerializer, CustomerSerializer, OrderSerializer, OrderItemSerializer, InventorySerializer, InventoryLogSerializer, SupplierSerializer, DeliverySerializer)

# Create your views here.
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        product = self.get_object()
        try:
            inventory = Inventory.objects.get(product=product)
            return Response(InventorySerializer(inventory).data)
        except Inventory.DoesNotExist:
            return Response({"detail": "No inventory found"}, status=404)
        
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        order = self.get_object()
        items = OrderItem.objects.filter(order=order)
        return Response(OrderItemSerializer(items, many=True).data)
    
    @action(detail=True, methods=['get'])
    def delivery_status(self, request, pk=None):
        order = self.get_object()
        if not hasattr(order, 'delivery'):
            return Response({"message": 'Delivery not yet assigned'})
        return Response(DeliverySerializer(order.delivery).data)

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    
class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    
class InventoryLogViewSet(viewsets.ModelViewSet):
    queryset = InventoryLog.objects.all()
    serializer_class = InventoryLogSerializer
    
class SupplierViewSet(viewsets.ModelViewSet):
    queryset = InventoryLog.objects.all()
    serializer_class = SupplierSerializer
    
    @action(detail=True, methods=['get'])
    def products(self, rewuest, pk=None):
        supplier=self.get_object()
        products=supplier.products.all()
        return Response(ProductSerializer(products, many=True).data)
    
class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer