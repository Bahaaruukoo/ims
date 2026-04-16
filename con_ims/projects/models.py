from core.models import TenantAwareModel
from django.db import models

from con_ims.settings import AUTH_USER_MODEL


# Create your models here.
class Project(TenantAwareModel):
    STATUS_CHOICES = [
        ("PLANNING", "Planning"),
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("ON_HOLD", "On Hold"),
        ("CANCELLED", "Cancelled"),
    ]

    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_by = models.ForeignKey(
        "core.CustomUser",
        null=True,
        on_delete=models.SET_NULL
    )
    updated_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="updated_project")
    
    def __str__(self):
        return self.name

class Site(TenantAwareModel):
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="sites"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="updated_site")

    def __str__(self):
        return f"{self.project.name} - {self.name}"
    
# -----------------------------
# Project Stage
# -----------------------------
class ProjectStage(TenantAwareModel):
    STATUS_CHOICES = [
        ("PLANNING", "Planning"),
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("ON_HOLD", "On Hold"),
        ("CANCELLED", "Cancelled"),
    ]
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="stages"
    )
    site = models.ForeignKey(
        "projects.Site",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default="PLANNING", choices=STATUS_CHOICES)

    class Meta:
        ordering = ["order"]
        unique_together = ("tenant", "project", "order")

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.order:
            last = ProjectStage.objects.filter(project=self.project).order_by("-order").first()
            self.order = (last.order + 1) if last else 1
        super().save(*args, **kwargs)

# -----------------------------
# Stage Material (BOQ per stage)
# -----------------------------
class StageMaterial(TenantAwareModel):
    stage = models.ForeignKey(
        "projects.ProjectStage",
        on_delete=models.CASCADE,
        related_name="materials"
    )

    item_variant = models.ForeignKey(
        "inventory.ItemVariant",
        on_delete=models.CASCADE
    )

    planned_quantity = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ("tenant", "stage", "item_variant")

    def __str__(self):
        return f"{self.stage} - {self.item_variant}"

        