from core.admin import tenant_admin_site
from django.contrib import admin

from .models import Membership


@admin.register(Membership, site=tenant_admin_site)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("project", "member", "site", "location")
    list_filter = ("project", "site", "location")
    search_fields = ("member__username", "project__name")


    def has_module_permission(self, request):
        return True
    
    # 🔒 Permissions
    def has_add_permission(self, request, obj=None):
        return True
    
    def has_view_permission(self, request, obj = ...):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True
    
from .models import Settings


@admin.register(Settings, site=tenant_admin_site)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ("StoreManagerCanApproveMaterialRequests",)
    list_filter = ("StoreManagerCanApproveMaterialRequests",)
    


    def has_module_permission(self, request):
        return True
    
    # 🔒 Permissions
    def has_add_permission(self, request, obj=None):
        return True
    
    def has_view_permission(self, request, obj = ...):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False
    