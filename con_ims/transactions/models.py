from time import timezone

from core.models import TenantAwareModel
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from projects.models import StageMaterial

from con_ims.settings import AUTH_USER_MODEL


# Create your models here.
class InventoryTransaction(TenantAwareModel):

    TYPE_CHOICES = [
        ("IN", "IN"),
        ("OUT", "OUT"),
        ("TRANSFER", "TRANSFER"),
    ]

    item_variant = models.ForeignKey(
        "inventory.ItemVariant",
        on_delete=models.CASCADE
    )

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=12, decimal_places=2)

    from_location = models.ForeignKey(
        "inventory.Location",
        related_name="from_transactions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    stage = models.ForeignKey(
        "projects.ProjectStage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    site = models.ForeignKey(
        "projects.Site", 
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    request_item = models.ForeignKey(
        "MaterialRequest",
        null=True,
        on_delete=models.SET_NULL
    )
    created_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="updated_transaction")
    date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        errors = {}

        # TRANSFER
        if self.type == "TRANSFER":
            if not self.from_location or not self.to_location:
                errors["from_location"] = "Required"
                errors["to_location"] = "Required"
            if self.from_location == self.to_location:
                errors["to_location"] = "Cannot transfer to same location"

        # IN
        if self.type == "IN" and not self.to_location:
            errors["to_location"] = "Required for IN"

        # OUT
        if self.type == "OUT":
            if not self.from_location:
                errors["from_location"] = "Required for OUT"

            if self.stage:
                planned = StageMaterial.objects.filter(
                    stage=self.stage,
                    item_variant=self.item_variant
                ).first()

                if planned:
                    used = InventoryTransaction.objects.filter(
                        stage=self.stage,
                        item_variant=self.item_variant,
                        type="OUT"
                    ).exclude(pk=self.pk).aggregate(
                        total=Sum("quantity")
                    )["total"] or 0

                    if used + self.quantity > planned.planned_quantity:
                        errors["quantity"] = (
                            f"Exceeds planned quantity. "
                            f"Planned: {planned.planned_quantity}, Used: {used}"
                        )

        # Stage-site consistency
        if self.stage and self.site:
            if self.stage.site != self.site:
                errors["stage"] = "Stage does not belong to selected site"

        if errors:
            raise ValidationError(errors)


class IncomingStock(TenantAwareModel):

    item_variant = models.ForeignKey(
        "inventory.ItemVariant",
        on_delete=models.CASCADE
    )

    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    price_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    location = models.ForeignKey(
        "inventory.Location",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    driver = models.CharField(max_length=255, null=True, blank=True)
    vehicle_number = models.CharField(max_length=255, null=True, blank=True)

    created_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="updated_incoming_stocks")
    date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        errors = {}

        if self.quantity <= 0:
            errors["quantity"] = "Quantity must be greater than zero."

        if not self.location:
            errors["location"] = "Location is required for incoming stock."

        if errors:
            raise ValidationError(errors)


class MaterialRequest(TenantAwareModel):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE)
    site = models.ForeignKey("projects.Site", on_delete=models.CASCADE)
    stage = models.ForeignKey("projects.ProjectStage", null=True, on_delete=models.SET_NULL)

    item_variant = models.ForeignKey("inventory.ItemVariant", on_delete=models.CASCADE)
    warehouse = models.ForeignKey("inventory.Location", on_delete=models.CASCADE)

    requested_quantity = models.DecimalField(max_digits=12, decimal_places=2)   
    date = models.DateTimeField(auto_now_add=True)
    approved_quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    requested_by = models.ForeignKey("core.CustomUser", on_delete=models.SET_NULL, null=True, related_name="requester")
    approved_by = models.ForeignKey("core.CustomUser", on_delete=models.SET_NULL, null=True, related_name="approver")
    status = models.CharField(max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
            ("DISPATCHED", "Dispatched"),
        ],
        default="PENDING"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        permissions = [
            ("approve_materialrequest", "Can approve material request"),
        ]

