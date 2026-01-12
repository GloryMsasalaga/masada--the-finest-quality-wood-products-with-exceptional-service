from django.db import models

from django.contrib.auth.models import User

# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    fullname = models.TextField(max_length=120)
    email = models.EmailField(max_length=120)
    # Password field removed - using Django Auth
    customer_type = models.CharField(max_length=120)
    customer_id = models.UUIDField(primary_key=True, editable=False)
    location = models.CharField(max_length=120)
    
    def __str__(self):
        return self.fullname
    
class admin(models.Model):
    email = models.EmailField(max_length=120)
    password = models.CharField(max_length=120)
    
    def __str__(self):
        return self.email

class Product(models.Model):
    product_id = models.UUIDField(primary_key=True, editable=False)
    ProductName = models.TextField(max_length=120)
    Price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    grade = models.CharField(max_length=50)
    ProductType = models.CharField(max_length=120)
    Category = models.CharField(max_length=120)
    Dimensions = models.CharField(max_length=120)
    stock_quantity = models.PositiveIntegerField(max_length=0)
    description = models.TextField(max_length=250)
    vendor = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    
    def __str__(self):
        return self.ProductName

class Staff(models.Model):
    employer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='staff_members')
    fullname = models.CharField(max_length=120)
    role = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_joined = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.fullname} - {self.role} at {self.employer.fullname}"

    
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name= "items")
    order_date = models. DateTimeField(auto_now_add=True)
    delivery_option = models.CharField(max_length=50) #Pickup/delivery
    payment_status = models.CharField(max_length=50) #pending / paid / failed
    order_status = models.CharField(max_length=50) #processing / delivered
    order_id = models.UUIDField(primary_key=True, editable=False)
    description = models.TextField(max_length=120)

    def __str__(self):
        return (f"Order #{self.OrderId}")
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name = "items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return (f"{self.product} X {self.quantity}")
      
class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_available = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(default=0)
    quantity_damaged = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    reorder_quantity = models.PositiveIntegerField(default=20)
    uom = models.CharField(max_length=50) # pcs, planks, m3, bundles
    warehouse_location = models.CharField(max_length=255, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return (f"Inventory for {self.product.ProductName}")
    
    @property
    def total_stock(self):
        return self.quantity_available + self.quantity_reserved
    
class InventoryLog(models.Model):
    ACTION_CHOICES = (
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('DAMAGED', 'Damaged Adjustment'),
        ('RESERVED', 'Reserved for Order'),
        ('RELEASED', 'Released from reservation'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    updated_by = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return (f"{self.action} - {self.product.ProductName} ({self.quantity})")
        
class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    delivery_date = models.DateField()
    delivery_address = models.CharField(max_length=255)
    driver_name = models.CharField(max_length=255)
    transport_cost = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_status = models.CharField(max_length=50)
    
    def __str__(self):
        return (f"Delivery for order #{self.order.OrderId}")
    
class Supplier(models.Model):
    name = models.CharField(max_length=120)
    contacts = models.CharField(max_length=120)
    email = models.EmailField(max_length=120)
    address = models.CharField(max_length=250)
    supplier_id = models.UUIDField(primary_key=True, editable=False)
    
    def __str__(self):
        return self.name
    
class ProductSupplier(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    supply_price = models.DecimalField(max_digits=10, decimal_places=2)
    supply_date = models.DateField
    
    class Meta:
        unique_together = ('product', 'supplier')
        
    def __str__(self):
        return (f"{self.product} from {self.supplier}")
    
    