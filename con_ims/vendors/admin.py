from core.admin_mixins import TenantAwareAdmin
from core.admin_sites import tenant_admin_site
# Register your models here.
from django.contrib import admin

from .models import Vendor


@admin.register(Vendor, site=tenant_admin_site)
class VendorAdmin(TenantAwareAdmin):

    list_display = ("name", "vendor_type", "contact", "phone", "email")
    search_fields = (
        "name",
        "contact",
        "vendor_type",
        "phone",
        "email",
    )

    list_filter = ("vendor_type",)

    ordering = ("name",)

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
    