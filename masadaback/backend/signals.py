from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem, Inventory, InventoryLog
from django.contrib.auth.models import User

#---------------------------------
#Auto-update inventory item when orderitem is created
#(STOCK_OUT)
#---------------------------------
@receiver(post_save, sender=OrderItem)
def reduce_stock_on_order(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        quantity = instance.quantity
        
        #get or create inventory
        inventory, _ = Inventory.objects.get_or_create(product=product, defaults={'quantity_available':0})
        
        #reduce available stock
        inventory.quantity_available -= quantity
        inventory.save()
        
        #log the change
        InventoryLog.objects.create(
            product=product,
            action='OUT',
            quantity=quantity,
            note=(f"Order #{instance.order.id} item purchased"),
        )
      
#------------------------
#Auto-update inventory when orderitem is deleted
#(Stock RETURN)  
#-----------------------   
@receiver(post_delete, sender=OrderItem)
def restore_stock_on_order_delete(sender, instance, **kwargs):
    product = instance.product
    quantity = instance.quantity
    
    #get inventory
    inventory, _ = Inventory.objects.get_or_create(
        product=product,
        defaults={'quantity_available': 0}
    )     
    
    #restore stock
    inventory.quantity_available += quantity
    inventory.save()
    
    #log the change
    InventoryLog.objects.create(
        product=product,
        action="IN",
        quantity=quantity,
        note=(f"Order #{instance.order.id} item removed / refunded."),
    )
    
#-------------------
#Auto-update inventory when inventorylog is created
#-------------------
@receiver(post_save, sender=InventoryLog)
def sync_inventory_from_log(sender, instance, created, **kwargs):
    if not created:
        return
    
    product = instance.product
    inventory, _ = Inventory.objects.get_or_create(
        product=product,
        defaults={'quantity_available':0}
    )
    
    if instance.action == "IN":
        inventory.quantity_available += instance.quantity
        
    elif instance.action == "OUT":
        inventory.quantity_available -= instance.quantity
        
    elif instance.action == "DAMAGED":
        inventory.quantity_available += instance.quantity
        
    elif instance.action == "RESERVED":
        inventory.quantity_available += instance.quantity
        
    elif instance.action == "RELEASED":
        inventory.quantity_available -=  instance.quantity
        
    inventory.save()