from core.admin_mixins import TenantAwareAdmin
from core.admin_sites import tenant_admin_site
from django.contrib import admin

from .models import InventoryTransaction


@admin.register(InventoryTransaction, site=tenant_admin_site)
class InventoryTransactionAdmin(TenantAwareAdmin):

    list_display = (
        "item_variant",
        "type",
        "quantity",
        "rate",
        "from_location",
        "project",
        "date",
    )

    search_fields = (
        "item_variant__name",
        "item_variant__item__name",
        "from_location__name",
        "project__name",
    )

    list_filter = (
        "type",
        "from_location",
        "project",
        "date",
    )

    autocomplete_fields = (
        "item_variant",
        "from_location",
        "project",
    )

    date_hierarchy = "date"
    ordering = ("-date",)

    # 🔒 Make readonly after creation
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_module_permission(self, request):
        return True
    
    # 🔒 Permissions
    def has_add_permission(self, request, obj=None):
        return True
    
    def has_view_permission(self, request, obj = ...):
        return True
    
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
'''
@admin.register(MaterialRequestItem, site=tenant_admin_site)
class MaterialRequestItemAdmin(TenantAwareAdmin):

    list_display = (
        "request",
        "item_variant",
        "requested_quantity",
        "request__requested_by",
        
    )

    search_fields = (
        "request__project__name",
        "item_variant__name",
        "item_variant__item__name",
        "requested_by__email",
    )

    list_filter = (
        "request__project",
        "date",
    )

    autocomplete_fields = (
        "item_variant",
    )

    date_hierarchy = "date"
    ordering = ("-date",)

    # 🔒 Make readonly after creation
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_module_permission(self, request):
        return True
    
    # 🔒 Permissions
    def has_add_permission(self, request, obj=None):
        return True
    
    def has_view_permission(self, request, obj = ...):
        return True
    
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
'''
