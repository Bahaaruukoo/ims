from core.admin_mixins import TenantAwareAdmin
from core.admin_sites import tenant_admin_site
# Register your models here.
from django.contrib import admin

from .models import CostCategory, CostEntry, Equipment, LaborType


# -----------------------------
# Cost Category Admin
# -----------------------------
@admin.register(CostCategory, site=tenant_admin_site)
class CostCategoryAdmin(TenantAwareAdmin):

    list_display = ("name", "requires_reference")

    search_fields = ("name",)

    list_filter = ("requires_reference",)

    ordering = ("name",)

    # 🔒 Lock after creation (prevents breaking reports)
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []
    def has_add_permission(self, request, obj=None):
        return True
    
    def has_module_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        """
        Disable hard delete.
        """
        return False
    def has_view_permission(self, request, obj = ...):
        return True

    def has_change_permission(self, request, obj = ...):
        return True
    
# -----------------------------
# Labor Type Admin
# -----------------------------
@admin.register(LaborType, site=tenant_admin_site)
class LaborTypeAdmin(TenantAwareAdmin):

    list_display = ("name", "default_rate")

    search_fields = ("name",)

    ordering = ("name",)

    # 🔒 Lock after creation
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_add_permission(self, request, obj=None):
        return True
    
    def has_module_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        """
        Disable hard delete.
        """
        return False
    def has_view_permission(self, request, obj = ...):
        return True

    def has_change_permission(self, request, obj = ...):
        return True
    
# -----------------------------
# Equipment Admin
# -----------------------------
@admin.register(Equipment, site=tenant_admin_site)
class EquipmentAdmin(TenantAwareAdmin):

    list_display = ("name", "default_rate")

    search_fields = ("name",)

    ordering = ("name",)

    # 🔒 Lock after creation
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_add_permission(self, request, obj=None):
        return True
    
    def has_module_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        """
        Disable hard delete.
        """
        return False
    def has_view_permission(self, request, obj = ...):
        return True

    def has_change_permission(self, request, obj = ...):
        return True
    
# -----------------------------
# Cost Entry Admin (MAIN)
# -----------------------------
@admin.register(CostEntry, site=tenant_admin_site)
class CostEntryAdmin(TenantAwareAdmin):

    list_display = (
        "project",
        "category",
        "quantity",
        "rate",
        "total_cost",
        "date",
    )

    search_fields = (
        "project__name",
        "category__name",
        "description",
    )

    list_filter = (
        "category",
        "project",
        "date",
    )

    autocomplete_fields = (
        "project",
        "category",
    )

    date_hierarchy = "date"

    ordering = ("-date",)

    # 🔒 Make readonly after creation (audit-safe)
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    # -----------------------------
    # Permissions
    # -----------------------------
        
    def has_module_permission(self, request, obj=None):
        return True
    
    def has_view_permission(self, request, obj=None):
        return True
    
    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False