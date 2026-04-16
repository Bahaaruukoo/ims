from core.models import TenantAwareModel
from django.db import models

from con_ims.settings import AUTH_USER_MODEL


# Create your models here.
class CostCategory(TenantAwareModel):
    name = models.CharField(max_length=100)
    requires_reference = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class CostEntry(TenantAwareModel):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE)
    category = models.ForeignKey(CostCategory, on_delete=models.CASCADE)

    # NEW 👇
    labor_type = models.ForeignKey(
        "LaborType",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    equipment = models.ForeignKey(
        "Equipment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    description = models.TextField(blank=True)

    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2)

    date = models.DateField()
    created_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="updated_cost_entry")


class LaborType(TenantAwareModel):
    name = models.CharField(max_length=100)
    default_rate = models.DecimalField(max_digits=10, decimal_places=2)


class Equipment(TenantAwareModel):
    name = models.CharField(max_length=100)
    default_rate = models.DecimalField(max_digits=10, decimal_places=2)

    