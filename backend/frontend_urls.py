# Frontend URLs for WoodHop Website
from django.urls import path
from . import frontend_views

urlpatterns = [
    # Main pages
    path('', frontend_views.home, name='home'),
    path('shop/', frontend_views.shop, name='shop'),
    path('product/<uuid:product_id>/', frontend_views.product_detail, name='product_detail'),
    
    # Authentication
    path('login/', frontend_views.user_login, name='login'),
    path('signup/', frontend_views.user_signup, name='signup'),
    path('logout/', frontend_views.user_logout, name='logout'),
    
    # User Dashboard
    path('dashboard/', frontend_views.dashboard, name='dashboard'),
    path('orders/', frontend_views.orders, name='orders'),
    path('order/<uuid:order_id>/', frontend_views.order_detail, name='order_detail'),
    
    # Shopping Cart
    path('cart/', frontend_views.cart, name='cart'),
    path('add-to-cart/', frontend_views.add_to_cart, name='add_to_cart'),
]