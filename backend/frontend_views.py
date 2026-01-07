# Frontend Views for WoodHop Website
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Customer, Order, OrderItem, Inventory
from .serializers import ProductSerializer
import json

def home(request):
    """Homepage with featured products"""
    featured_products = Product.objects.all()[:6]  # Show first 6 products
    product_types = Product.objects.values_list('ProductType', flat=True).distinct()
    
    context = {
        'featured_products': featured_products,
        'product_types': product_types,
    }
    return render(request, 'frontend/home.html', context)

def shop(request):
    """Product catalog/shop page"""
    products = Product.objects.all()
    
    # Filter by product type if specified
    product_type = request.GET.get('type')
    if product_type:
        products = products.filter(ProductType__icontains=product_type)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(ProductName__icontains=search_query) |
            Q(ProductType__icontains=search_query) |
            Q(Category__icontains=search_query)
        )
    
    # Get distinct product types for filter
    product_types = Product.objects.values_list('ProductType', flat=True).distinct()
    categories = Product.objects.values_list('Category', flat=True).distinct()
    
    context = {
        'products': products,
        'product_types': product_types,
        'categories': categories,
        'current_type': product_type,
        'search_query': search_query,
    }
    return render(request, 'frontend/shop.html', context)

def product_detail(request, product_id):
    """Individual product detail page"""
    product = get_object_or_404(Product, product_id=product_id)
    
    # Get inventory information
    try:
        inventory = Inventory.objects.get(product=product)
    except Inventory.DoesNotExist:
        inventory = None
    
    # Get related products (same category)
    related_products = Product.objects.filter(
        Category=product.Category
    ).exclude(product_id=product_id)[:4]
    
    context = {
        'product': product,
        'inventory': inventory,
        'related_products': related_products,
    }
    return render(request, 'frontend/product_detail.html', context)

def user_login(request):
    """User login page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Try to authenticate with Customer model
        try:
            customer = Customer.objects.get(email=email, password=password)
            request.session['customer_id'] = str(customer.customer_id)
            request.session['customer_name'] = customer.fullname
            messages.success(request, f'Welcome back, {customer.fullname}!')
            return redirect('dashboard')
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'frontend/login.html')

def user_signup(request):
    """User signup page"""
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        customer_type = request.POST.get('customer_type', 'Individual')
        location = request.POST.get('location')
        
        # Check if email already exists
        if Customer.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'frontend/signup.html')
        
        # Create new customer
        import uuid
        customer = Customer.objects.create(
            customer_id=uuid.uuid4(),
            fullname=fullname,
            email=email,
            password=password,
            customer_type=customer_type,
            location=location
        )
        
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    
    return render(request, 'frontend/signup.html')

def user_logout(request):
    """User logout"""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def dashboard(request):
    """User dashboard"""
    # Check if customer is logged in via session
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login')
    
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        recent_orders = Order.objects.filter(customer=customer).order_by('-order_date')[:5]
        
        context = {
            'customer': customer,
            'recent_orders': recent_orders,
        }
        return render(request, 'frontend/dashboard.html', context)
    except Customer.DoesNotExist:
        request.session.flush()
        return redirect('login')

def orders(request):
    """User orders page"""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login')
    
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        orders = Order.objects.filter(customer=customer).order_by('-order_date')
        
        context = {
            'customer': customer,
            'orders': orders,
        }
        return render(request, 'frontend/orders.html', context)
    except Customer.DoesNotExist:
        return redirect('login')

def order_detail(request, order_id):
    """Individual order detail"""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login')
    
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        order = get_object_or_404(Order, order_id=order_id, customer=customer)
        order_items = OrderItem.objects.filter(order=order)
        
        context = {
            'order': order,
            'order_items': order_items,
            'customer': customer,
        }
        return render(request, 'frontend/order_detail.html', context)
    except Customer.DoesNotExist:
        return redirect('login')

# AJAX Views for dynamic functionality
def add_to_cart(request):
    """Add product to cart (stored in session)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        try:
            product = Product.objects.get(product_id=product_id)
            
            # Get or create cart in session
            cart = request.session.get('cart', {})
            
            if str(product_id) in cart:
                cart[str(product_id)]['quantity'] += quantity
            else:
                cart[str(product_id)] = {
                    'name': product.ProductName,
                    'price': float(product.Price_per_unit),
                    'quantity': quantity,
                    'product_type': product.ProductType,
                }
            
            request.session['cart'] = cart
            cart_count = sum(item['quantity'] for item in cart.values())
            
            return JsonResponse({
                'success': True,
                'message': f'{product.ProductName} added to cart',
                'cart_count': cart_count
            })
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def cart(request):
    """Shopping cart page"""
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, item in cart.items():
        subtotal = item['price'] * item['quantity']
        total += subtotal
        cart_items.append({
            'product_id': product_id,
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'product_type': item['product_type'],
            'subtotal': subtotal
        })
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': len(cart_items)
    }
    return render(request, 'frontend/cart.html', context)