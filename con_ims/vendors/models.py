from core.models import TenantAwareModel
from django.db import models


# Create your models here.
class Vendor(TenantAwareModel):
        
    VENDOR_TYPE_CHOICES = [
        ("SUPPLIER", "Supplier"),
        ("CONTRACTOR", "Contractor"),
        ("TRANSPORT", "Transport"),
        ("OTHER", "Other"),
    ]

    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=255, blank=True)
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPE_CHOICES )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)