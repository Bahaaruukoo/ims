# core/admin_sites.py
from core.session.admin_sessions import AdminSessionViewsMixin
from django.contrib.admin import AdminSite


class PlatformAdminSite(AdminSessionViewsMixin, AdminSite):
    site_header = "Utility Platform Admin"
    site_title = "Platform Admin"
    index_title = ""

class TenantAdminSite(AdminSessionViewsMixin, AdminSite):
    site_header = "Tenant Admin"
    site_title = "Tenant Admin"
    index_title = ""

    def each_context(self, request):
        context = super().each_context(request)

        tenant = getattr(request, "tenant", None)
        branch = getattr(request, "branch", None)

        if tenant:
            # Tenant admin
            context["site_header"] = f"{tenant.name} Admin"
            context["site_title"] = f"{tenant.name} Admin"
        else:
            # Fallback (should rarely happen)
            context["site_header"] = "Admin"
            context["site_title"] = " Admin"

        return context
    
class TenantDomainAdminSite(AdminSessionViewsMixin, AdminSite):
    site_header = "Domain Admin"
    site_title = "Domain Admin"
    index_title = "Domain Administration"

platform_admin_site = PlatformAdminSite(name="platform_admin")
tenant_admin_site = TenantAdminSite(name="tenant_admin")
tenant_domain_admin_site = TenantDomainAdminSite(name="tenant_domain_admin")