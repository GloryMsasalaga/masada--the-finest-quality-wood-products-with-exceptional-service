# Frontend URLs for WoodHop Website
from django.urls import path
from django.contrib.auth import views as auth_views
from . import frontend_views
from .views import custom_404_view

urlpatterns = [
    # Main pages
    path('', frontend_views.home, name='home'),
    path('shop/', frontend_views.shop, name='shop'),
    path('product/<uuid:product_id>/', frontend_views.product_detail, name='product_detail'),
    
    # Authentication
    path('login/', frontend_views.user_login, name='login'),
    path('signup/', frontend_views.user_signup, name='signup'),
    path('logout/', frontend_views.user_logout, name='logout'),
    path('verify-account/<uuid:customer_id>/', frontend_views.verify_account, name='verify_account'),
    path('resend-verification/<uuid:customer_id>/', frontend_views.resend_verification, name='resend_code'),
    
    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='frontend/password_reset_form.html',
             email_template_name='frontend/password_reset_email.txt',
             subject_template_name='frontend/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='frontend/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='frontend/password_reset_confirm.html',
             success_url='/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='frontend/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Magic Link Login (Passwordless)
    path('login-email/', frontend_views.request_token_login, name='request_token_login'),
    path('verify-login/<uidb64>/<token>/', frontend_views.verify_token_login, name='verify_token_login'),
    
    # Business Tools
    path('add-product/', frontend_views.add_product, name='add_product'),
    path('add-staff/', frontend_views.add_staff, name='add_staff'),
    
    # User Dashboard
    path('dashboard/', frontend_views.dashboard, name='dashboard'),
    path('bulk-order/', frontend_views.bulk_order, name='bulk_order'),
    path('orders/', frontend_views.orders, name='orders'),
    path('order/<uuid:order_id>/', frontend_views.order_detail, name='order_detail'),
    
    # Shopping Cart
    path('cart/', frontend_views.cart, name='cart'),
    path('add-to-cart/', frontend_views.add_to_cart, name='add_to_cart'),
    path('api/cart-count/', frontend_views.get_cart_count, name='get_cart_count'),
    path('page-not-found/', custom_404_view, name='page_not_found'),
]