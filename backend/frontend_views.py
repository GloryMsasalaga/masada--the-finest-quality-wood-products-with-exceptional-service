# Frontend Views for WoodHop Website
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, F, Count
from .models import Product, Customer, Order, OrderItem, Inventory, Staff
from .serializers import ProductSerializer
from django.utils import timezone
from datetime import timedelta
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
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Ensure customer profile exists
            if hasattr(user, 'customer'):
                messages.success(request, f'Welcome back, {user.customer.fullname}!')
                return redirect('dashboard')
            else:
                messages.warning(request, 'User profile incomplete.')
                return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'frontend/login.html', {'email': email})
    
    return render(request, 'frontend/login.html')

def user_signup(request):
    """User signup page"""
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        customer_type = request.POST.get('customer_type', 'Individual')
        location = request.POST.get('location')
        
        # Check if email/username already exists
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'frontend/signup.html')
        
        try:
            # Create User
            user = User.objects.create_user(username=email, email=email, password=password)
            user.first_name = fullname.split(' ')[0] if ' ' in fullname else fullname
            user.save()
            
            # Create Customer Profile
            import uuid
            Customer.objects.create(
                user=user,
                customer_id=uuid.uuid4(),
                fullname=fullname,
                email=email,
                customer_type=customer_type,
                location=location
            )
            
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'frontend/signup.html')
    
    return render(request, 'frontend/signup.html')

def user_logout(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required(login_url='login')
def dashboard(request):
    """User dashboard"""
    try:
        customer = request.user.customer
        
        # Business Dashboard Logic
        if customer.customer_type == 'Business':
            # Get products owned by this business
            products = Product.objects.filter(vendor=customer)
            inventory_items = Inventory.objects.filter(product__vendor=customer)
            staff_members = Staff.objects.filter(employer=customer)
            
            # Weekly stats
            today = timezone.now()
            last_week = today - timedelta(days=7)
            
            # Sales (OrderItems for this vendor's products)
            recent_sales = OrderItem.objects.filter(
                product__vendor=customer,
                order__order_date__gte=last_week
            )
            
            weekly_earnings = sum(item.subtotal for item in recent_sales)
            weekly_earnings = round(float(weekly_earnings), 2)
            weekly_orders_count = recent_sales.values('order').distinct().count()
            
            # Graph Data (Last 7 Days)
            graph_labels = []
            graph_data = []
            
            for i in range(7):
                day = today - timedelta(days=i)
                # Filter sales for that specific day
                # simple date comparison; for robust timezone handling use range
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                daily_sales = OrderItem.objects.filter(
                    product__vendor=customer,
                    order__order_date__range=(day_start, day_end)
                )
                daily_total = sum(item.subtotal for item in daily_sales)
                
                graph_labels.insert(0, day.strftime('%a')) # Mon, Tue...
                graph_data.insert(0, float(daily_total))
            
            total_products = products.count()
            # Low stock items (assuming reorder_level logic exists in Inventory model)
            # Using F expression if reorder_level is a field, else fallback or simple comparison if fixed.
            # Inventory model has reorder_level.
            low_stock_count = inventory_items.filter(quantity_available__lt=F('reorder_level')).count()
            
            context = {
                'customer': customer,
                'inventory_items': inventory_items,
                'staff_members': staff_members,
                'weekly_earnings': weekly_earnings,
                'weekly_orders_count': weekly_orders_count,
                'total_products': total_products,
                'low_stock_count': low_stock_count,
                'graph_labels': json.dumps(graph_labels),
                'graph_data': json.dumps(graph_data),
                'sales_growth': 12, # Placeholder calculation
                'sales_growth_icon': 'up',
                'sales_growth_color': 'success'
            }
            return render(request, 'frontend/business_dashboard.html', context)
        
        # Standard Customer Logic
        else:
            recent_orders = Order.objects.filter(customer=customer).order_by('-order_date')[:5]
            
            context = {
                'customer': customer,
                'recent_orders': recent_orders,
            }
            return render(request, 'frontend/dashboard.html', context)

    except Exception as e:
        print(f"Dashboard Error: {e}") # Debugging
        messages.error(request, "Customer profile not found.")
        return redirect('home')

@login_required(login_url='login')
def orders(request):
    """User orders page"""
    try:
        customer = request.user.customer
        orders = Order.objects.filter(customer=customer).order_by('-order_date')
        
        context = {
            'customer': customer,
            'orders': orders,
        }
        return render(request, 'frontend/orders.html', context)
    except Exception:
        return redirect('home')

@login_required(login_url='login')
def order_detail(request, order_id):
    """Individual order detail"""
    try:
        customer = request.user.customer
        order = get_object_or_404(Order, order_id=order_id, customer=customer)
        order_items = OrderItem.objects.filter(order=order)
        
        context = {
            'order': order,
            'order_items': order_items,
            'customer': customer,
        }
        return render(request, 'frontend/order_detail.html', context)
    except Exception:
        return redirect('orders')

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

@login_required
def add_product(request):
    """Allow business users to add products"""
    if request.method == 'POST':
        try:
            customer = request.user.customer
            if customer.customer_type != 'Business':
                return JsonResponse({'success': False, 'message': 'Unauthorized'})
                
            import uuid
            product = Product.objects.create(
                product_id=uuid.uuid4(),
                ProductName=request.POST.get('name'),
                Price_per_unit=request.POST.get('price'),
                grade=request.POST.get('grade', 'Standard'),
                ProductType=request.POST.get('type'),
                Category=request.POST.get('category'),
                Dimensions=request.POST.get('dimensions'),
                stock_quantity=0, # Initial stock logic handled by inventory usually, but model has it
                description=request.POST.get('description'),
                vendor=customer
            )
            
            # Create initial inventory record
            Inventory.objects.create(
                product=product,
                quantity_available=int(request.POST.get('quantity', 0)),
                uom=request.POST.get('uom', 'pcs')
            )
            
            messages.success(request, 'Product added successfully.')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
            return redirect('dashboard')
            
    return redirect('dashboard')

@login_required
def add_staff(request):
    """Allow business users to add staff"""
    if request.method == 'POST':
        try:
            customer = request.user.customer
            if customer.customer_type != 'Business':
                return JsonResponse({'success': False, 'message': 'Unauthorized'})
                
            Staff.objects.create(
                employer=customer,
                fullname=request.POST.get('fullname'),
                role=request.POST.get('role'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone')
            )
            
            messages.success(request, 'Staff member added successfully.')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding staff: {str(e)}')
            return redirect('dashboard')
            
    return redirect('dashboard')
