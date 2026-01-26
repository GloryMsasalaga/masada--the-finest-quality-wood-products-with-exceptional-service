# from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.urls import path, include
from .views import (ProductViewSet, CustomerViewSet, OrderItemViewSet, OrderViewSet, InventoryViewSet, InventoryLogViewSet, SupplierViewSet, DeliveryViewSet)

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')
router.register(r'supplier', SupplierViewSet, basename='supplier')
router.register(r'customer', CustomerViewSet, basename='customers')
router.register(r'order', OrderViewSet, basename='order')
# router.register(r'order-item', OrderItemViewSet, basename='order-item')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'inventory-log', InventoryLogViewSet, basename='inventory-log')
router.register(r'delivery', DeliveryViewSet, basename='delivery')

#nested supplier -> products
# Parent is 'supplier', so we must use 'supplier' here
supplier_router = routers.NestedDefaultRouter(router, 'supplier', lookup='supplier')
supplier_router.register('products', ProductViewSet, basename='supplier-products')

#nested order -> items
# Parent is 'order', so we must use 'order' here. Also fixed 'routers' -> 'router'
order_router = routers.NestedDefaultRouter(router, 'order', lookup='order')
order_router.register('items', OrderItemViewSet, basename='order-item')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(supplier_router.urls)),
    path('', include(order_router.urls)),
]


