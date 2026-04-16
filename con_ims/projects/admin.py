from core.admin_mixins import TenantAwareAdmin
from core.admin_sites import tenant_admin_site
# Register your models here.
from django.contrib import admin

from .models import Project, ProjectStage, Site, StageMaterial


class StageMaterialInline(admin.TabularInline):
    model = StageMaterial
    extra = 1
    fields = ("item_variant", "planned_quantity")
    autocomplete_fields = ("item_variant",)

class ProjectStageInline(admin.TabularInline):
    model = ProjectStage
    extra = 1
    fields = ("name", "description")
    show_change_link = True  # 🔥 IMPORTANT (opens stage with materials)


@admin.register(ProjectStage, site=tenant_admin_site)
class ProjectStageAdmin(TenantAwareAdmin):

    list_display = ("project", "name", "order")
    search_fields = ("name", "project__name")
    list_filter = ("project",)
    ordering = ("project", "order")
    autocomplete_fields = ("project",)
    inlines = [StageMaterialInline]

    # 🔒 Lock after creation
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []
    
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
    
@admin.register(StageMaterial, site=tenant_admin_site)
class StageMaterialAdmin(TenantAwareAdmin):

    list_display = ("stage", "item_variant", "planned_quantity")

    search_fields = (
        "stage__name",
        "stage__project__name",
        "item_variant__name",
        "item_variant__item__name",
    )

    list_filter = ("stage", "item_variant")

    autocomplete_fields = ("stage", "item_variant")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []
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
    

@admin.register(Project, site=tenant_admin_site)
class ProjectAdmin(TenantAwareAdmin):
    list_display = ("name", "start_date", "end_date", "status")
    search_fields = ("name", )
    list_filter = ("status", "start_date")
    ordering = ("-start_date",)
    inlines = [ProjectStageInline]
  
    # Required for autocomplete_fields used in other apps (like Location)
    # This enables fast lookup when selecting project
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

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


@admin.register(Site, site=tenant_admin_site)
class SiteAdmin(TenantAwareAdmin):

    list_display = ("name", "project")

    search_fields = (
        "name",
        "project__name",
    )

    list_filter = ("project",)
    autocomplete_fields = ("project",)
    ordering = ("project", "name")
    inlines = [ProjectStageInline]

    # 🔒 Lock after creation (optional but recommended)
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []


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
