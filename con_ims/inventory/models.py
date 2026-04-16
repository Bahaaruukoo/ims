from core.models import TenantAwareModel
from django.core.validators import MinValueValidator
from django.db import models


# Create your models here.
class Item(TenantAwareModel):
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class ItemVariant(TenantAwareModel):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # e.g. 10mm
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    attributes = models.JSONField(default=dict, blank=True)
    sku = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.item.name} - {self.name}"
    
    class Meta:
        unique_together = ("tenant", "sku")

#store locations like warehouse, store, etc. 
# Each location can have multiple stocks of different item variants.    
class Location(TenantAwareModel):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="locations" 
    )

    def __str__(self):
        return self.name
    
class Stock(TenantAwareModel):
    item_variant = models.ForeignKey(ItemVariant, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    class Meta:
        unique_together = ("item_variant", "location")
    
    