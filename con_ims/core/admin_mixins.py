from django.contrib import admin
from django.db import connection


class TenantAwareAdmin(admin.ModelAdmin):
    """
    Base admin that:
    - filters by current tenant
    - auto-assigns tenant on save
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if connection.schema_name == "public":
            return qs.none()
        return qs.filter(tenant=request.tenant)

    def save_model(self, request, obj, form, change):
        if not obj.tenant_id:
            obj.tenant = request.tenant
        super().save_model(request, obj, form, change)