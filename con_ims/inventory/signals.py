from django.db.models.signals import post_save
from django.dispatch import receiver
from transactions.models import IncomingStock, InventoryTransaction

from .models import Stock


@receiver(post_save, sender=IncomingStock)
def update_stock_on_incoming(sender, instance, created, **kwargs):
    if not created:
        return  # Only run on creation

    tenant = instance.tenant
    item_variant = instance.item_variant
    location = instance.location

    # Get or create stock entry
    stock, _ = Stock.objects.get_or_create(
        tenant=tenant,
        item_variant=item_variant,
        location=location,
        defaults={"quantity": 0}
    )

    # Update stock totals
    stock.quantity += instance.quantity
    #stock.total_available += instance.quantity
    stock.save()

@receiver(post_save, sender=InventoryTransaction)
def update_stock_on_dispatch(sender, instance, created, **kwargs):
    if not created:
        return  # Only run on creation

    tenant = instance.tenant
    item_variant = instance.item_variant
    location = instance.from_location

    # Get stock entry
    stock = Stock.objects.filter(
        tenant=tenant,
        item_variant=item_variant,
        location=location
    ).first()

    # Update stock totals
    stock.quantity -= instance.quantity
    if stock.quantity < 0:
        raise ValueError("Invalid approval quantity")
    #stock.total_available += instance.quantity
    stock.save()
