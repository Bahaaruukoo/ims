# utility/urls.py
from core import views as core_views
from core.admin import platform_admin_site  # ✅ platform admin site (custom)
from core.admin import tenant_admin_site  # ✅ tenant admin site (custom)
from django.urls import include, path
from tenant_manager.admin import tenant_domain_admin_site

urlpatterns = [
    # Tenant home pages
    # ✅ Tenant admin (TENANT DOMAINS ONLY)
    path("admin/", tenant_admin_site.urls),
    
    #path("b/<slug:branch_code>/admin/", tenant_domain_admin_site.urls),
    # Auth / allauth
    path("accounts/login/", core_views.TenantLoginView.as_view(), name="account_login"),
    path("accounts/profile/", core_views.profile_view, name="profile"),
    path("accounts/profile/edit/", core_views.profile_edit, name="profile_edit"),
    path("accounts/dashboard/", core_views.account_dashboard, name="account_dashboard"),
    path("accounts/", include("allauth.urls")),

    path("transactions/", include("transactions.urls")),
    path("store/", include("inventory.urls")),
    path("core/", include("core.urls")),
    path("projects/", include("projects.urls")),
    path("reports/", include("reports.urls")),
    path("", include("utils.urls")),

]
'''
handler400 = "portal.views.bad_request"
handler403 = "portal.views.permission_denied"
handler404 = "portal.views.page_not_found"
handler500 = "portal.views.server_error"
'''