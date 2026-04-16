from core.admin_mixins import TenantAwareAdmin
from core.admin_sites import tenant_admin_site
from django.contrib import admin

from .forms import ItemVariantForm
from .models import Item, ItemVariant, Location, Stock

# -----------------------------
# Item Variant Inline
# -----------------------------

class ItemVariantInline(admin.TabularInline):
    model = ItemVariant
    form = ItemVariantForm
    extra = 1
    fields = ("name", "sku", "attributes")
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return super().has_add_permission(request, obj)
    def has_module_permission(self, request):
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
# Item Variant Admin
# -----------------------------

@admin.register(ItemVariant, site=tenant_admin_site)
class ItemVariantAdmin(TenantAwareAdmin):
    form = ItemVariantForm

    list_display = ("item", "name", "sku", "formatted_attributes")
    search_fields = ("name", "sku", "item__name")
    list_filter = ("item",)
    autocomplete_fields = ("item",)

    def formatted_attributes(self, obj):
        return obj.attributes

    formatted_attributes.short_description = "Attributes"
    
    def has_module_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        """
        Disable hard delete.
        """
        return False
    def has_view_permission(self, request, obj = ...):
        return True
    def has_add_permission(self, request, obj=None):
        return True
    def has_change_permission(self, request, obj = ...):
        return True
    
# -----------------------------
# Item Admin
# -----------------------------
@admin.register(Item, site=tenant_admin_site)
class ItemAdmin(TenantAwareAdmin):
    list_display = ("name", "category", "unit")
    search_fields = ("name", "category")
    list_filter = ("category",)
    inlines = [ItemVariantInline]

    def has_module_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        """
        Disable hard delete.
        """
        return False
    def has_view_permission(self, request, obj = ...):
        return True
    def has_add_permission(self, request, obj=None):
        return True
    def has_change_permission(self, request, obj = ...):
        return True
    

# -----------------------------
# Location Admin
# -----------------------------
@admin.register(Location, site=tenant_admin_site)
class LocationAdmin(TenantAwareAdmin):
    list_display = ("name", "project")
    search_fields = ("name",)
    list_filter = ("project",)

    autocomplete_fields = ("project",)

    def has_module_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        """
        Disable hard delete.
        """
        return False
    def has_view_permission(self, request, obj = ...):
        return True
    def has_add_permission(self, request):
        return True
    def has_change_permission(self, request, obj = ...):
        return True


@admin.register(Stock, site=tenant_admin_site)
class StockAdmin(TenantAwareAdmin):

    list_display = ("item_variant", "location", "quantity")

    search_fields = (
        "location__name",
        "item_variant__name",
        "item_variant__item__name",
    )

    list_filter = ("location", "item_variant")

    # -----------------------------
    # Permissions
    # -----------------------------

    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Disable hard delete.
        """
        return False