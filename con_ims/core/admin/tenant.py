from collections import defaultdict
from urllib import request

from core.admin_sites import tenant_admin_site
from core.forms import ProfileInlineForm, TenantRolePermissionAdminForm
from core.models import (CustomUser, Profile, Role, TenantRolePermission,
                         TenantUserRole)
from core.session.admin_mixins import UserSessionAdminMixin
from core.session.session_utils import (list_active_sessions_for_user,
                                        revoke_all_sessions_for_user)
from django.conf import settings
# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Permission
from django.contrib.sessions.models import Session
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms.models import BaseInlineFormSet
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from pyexpat.errors import messages
from tenant_manager.models import Tenant

TENANT_PERMISSION_APPS = settings.TENANT_APPS

def is_tenant_admin(request) -> bool:
    u = getattr(request, "user", None)
    return bool(
        u
        and u.is_authenticated
        and getattr(u, "is_staff", False)
        and not getattr(u, "is_platform_admin", False)
    ) or bool(
        u
        and u.is_authenticated
        and getattr(u, "is_staff", False)
        and not getattr(u, "is_admin", False)
    )


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 1
    form = ProfileInlineForm
    can_delete = False
    verbose_name = "User Detail"
    verbose_name_plural = "User Details"
    classes = ()  # expanded
    fields = ("phone", "address", "department", "position", "picture")

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

class TenantUserRoleInlineFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()

        seen = set()

        for form in self.forms:

            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            role = form.cleaned_data.get("role")
            instance = form.instance
            user = self.instance
            tenant = getattr(self.request, "tenant", None)

            if not role or not tenant:
                continue

            # prevent duplicates inside the same form submission
            key = (role.id)
            if key in seen:
                raise ValidationError(f"{role.name} role assigned twice.")

            seen.add(key)

            # prevent duplicates already in DB (ignore current instance)
            if user and user.pk:  # ensure user is saved
                if TenantUserRole.objects.filter(
                    user=user,
                    role=role,
                    tenant=tenant
                ).exclude(pk=instance.pk).exists():
                    raise ValidationError(
                        f"{role.name} role already assigned to this user."
                    )
                
class TenantUserRoleInline(admin.TabularInline):
    model = TenantUserRole
    formset = TenantUserRoleInlineFormSet
    fk_name = "user"
    extra = 1
    can_delete = True
    verbose_name = "Role"
    verbose_name_plural = "Roles"
    fields = ("role",)  # no tenant field

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request
        return formset
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return qs.none()
        return qs.filter(tenant=tenant).select_related("role")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "role":                
    
            kwargs["queryset"] = Role.objects.exclude(
                name="PLATFORM_ADMIN"
            ).order_by("name")

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_formset(self, request, form, formset, change):
        """
        Force tenant=request.tenant and ignore duplicate role assignments gracefully.
        """
        tenant = getattr(request, "tenant", None)
        parent_user = form.instance

        instances = formset.save(commit=False)

        for inst in instances:
            inst.user = parent_user
            inst.tenant = tenant  # force tenant

            # prevent duplicate crash
            TenantUserRole.objects.get_or_create(
                user=inst.user,
                tenant=inst.tenant,
                role=inst.role,
            )

        # deletions
        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

class TenantUserAdmin(BaseUserAdmin):
    model = CustomUser
    inlines = [ProfileInline, TenantUserRoleInline] 

    ordering = ("email",)
    search_fields = ("email",)
    list_display = ( "email", "first_name", "middle_name", "last_name", "is_active", "is_staff", "is_admin")

    fieldsets = (
        (None, {"fields": ("first_name", "middle_name", "last_name", "email", "password")}),
        (_("Status"), {"fields": ("is_active", "is_staff", "is_admin")}),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("first_name", "middle_name", "last_name", "email", "password1", "password2"),
        }),
         (_("Status"), {"fields": ("is_active", "is_staff", "is_admin")}),
    )
    #actions = None

    # ----------------------------
    # Branch helpers (added)
    # ----------------------------
    

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return qs.none()

        qs = qs.filter(tenant=tenant, is_platform_admin=False)
         
        # Tenant admin sees all tenant users
        return qs
    
    
    def save_model(self, request, obj, form, change):
        obj.tenant = request.tenant
        obj.is_platform_admin = False
        #obj.is_staff = True  # tenant admin-managed users can access tenant admin if needed
        super().save_model(request, obj, form, change)

    def has_module_permission(self, request): 
        return is_tenant_admin(request)

    def has_view_permission(self, request, obj=None): 
        return is_tenant_admin(request) 

    def has_add_permission(self, request):
        return is_tenant_admin(request)

    def has_change_permission(self, request, obj=None):
        return is_tenant_admin(request)        

    def has_delete_permission(self, request, obj=None):
        return is_tenant_admin(request)

    # ----------------------------
    # Session UI link (unchanged)
    # ----------------------------
    def sessions_link(self, obj):
        # Works no matter whether this AdminSite is platform_admin or tenant_admin
        url = reverse(
            f"{self.admin_site.name}:core_customuser_sessions",
            args=[obj.pk]
        )
        return format_html('<a class="button" href="{}">Sessions</a>', url)
    sessions_link.short_description = "Sessions"

    # ----------------------------
    # Session tenant boundary (unchanged)
    # ----------------------------
    def _can_manage_user(self, request, user_obj) -> bool:
        tenant = getattr(request, "tenant", None)
        return bool(
            tenant
            and user_obj.tenant_id == tenant.id
            and not getattr(user_obj, "is_platform_admin", False)
        )


class TenantRolePermissionTenantAdmin(admin.ModelAdmin):

    form = TenantRolePermissionAdminForm
    list_display = ("role",)
    filter_horizontal = ("permissions",)

    def get_queryset(self, request):

        qs = super().get_queryset(request)

        if not getattr(request, "tenant", None):
            return qs.none()

        return qs.filter(tenant=request.tenant)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "role":
    
            kwargs["queryset"] = Role.objects.exclude(
                name="PLATFORM_ADMIN"
            ).order_by("name")

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):

        if db_field.name == "permissions":

            kwargs["queryset"] = Permission.objects.filter(
                content_type__app_label__in=TENANT_PERMISSION_APPS
            ).order_by("content_type__app_label", "codename")

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields.pop("tenant", None)
        return form

    def save_model(self, request, obj, form, change):
        tenant = request.tenant
        existing = TenantRolePermission.objects.filter(
            tenant=tenant,
            role=obj.role
        ).first()

        if existing and not change:
            # Reuse existing object instead of creating new
            obj.pk = existing.pk

        obj.tenant = tenant
        super().save_model(request, obj, form, change)
        
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        template = form.cleaned_data.get("template")

        if template:
            obj.permissions.set(template.permissions.all())

    def has_module_permission(self, request):
        return is_tenant_admin(request)

    def has_view_permission(self, request, obj=None):
        return is_tenant_admin(request)

    def has_add_permission(self, request):
        return is_tenant_admin(request)

    def has_change_permission(self, request, obj=None):
        return is_tenant_admin(request)

    def has_delete_permission(self, request, obj=None):
        return is_tenant_admin(request) 
    
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at",  "action", "actor", "target_repr")
    list_filter = ("tenant", "action", "created_at")
    search_fields = (
        "actor__email",
        "target_repr",
        "target_model",
        "target_pk",
        "path",
        "ip_address",
    )
    ordering = ("-created_at",)

    readonly_fields = (
        
        "actor",
        "action",
        "target_model",
        "target_pk",
        "target_repr",
        "ip_address",
        "user_agent",
        "path",
        "method",
        "metadata",
        "created_at",
    )
    exclude = ("tenant",)
    def has_view_permission(self, request, obj=None):
        return True  # 
    
    # Logs are immutable from admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # Optional: only platform admin can delete (you can also return False always)
    def has_delete_permission(self, request, obj=None):
        return bool(getattr(request.user, "is_platform_admin", False))

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Platform admin sees all
        if getattr(request.user, "is_platform_admin", False):
            return qs

        # Tenant admin sees only own tenant
        tenant = getattr(request, "tenant", None) or getattr(request.user, "tenant", None)
        if tenant:
            return qs.filter(tenant=tenant)

        return qs.none()

    def get_list_filter(self, request):
        """
        Tenant admins should NOT even see a tenant filter,
        platform admins can filter by tenant.
        """
        if getattr(request.user, "is_platform_admin", False):
            return self.list_filter
        # hide tenant filter for tenant admins
        return tuple(x for x in self.list_filter if x != "tenant")

def _session_user_id(session: Session) -> int | None:
    try:
        data = session.get_decoded()
        uid = data.get("_auth_user_id")
        return int(uid) if uid is not None else None
    except Exception:
        return None


def _tenant_user_ids(request) -> set[int]:
    tenant = getattr(request, "tenant", None)
    if not tenant:
        return set()
    return set(
        CustomUser.objects.filter(
            tenant=tenant,
            is_platform_admin=False,
        ).values_list("id", flat=True)
    )

class SessionAdmin(admin.ModelAdmin):
    list_display = ("session_key", "expire_date")
    search_fields = ("session_key",)
    ordering = ("-expire_date",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # show only active sessions by default
        return qs.filter(expire_date__gte=timezone.now())

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "by-user/",
                self.admin_site.admin_view(self.sessions_by_user_view),
                name="tenant_sessions_by_user",
            ),
            path(
                "by-user/<int:user_id>/",
                self.admin_site.admin_view(self.sessions_for_user_view),
                name="tenant_sessions_for_user",
            ),
            path(
                "by-user/<int:user_id>/revoke/",
                self.admin_site.admin_view(self.revoke_user_sessions_view),
                name="tenant_revoke_user_sessions",
            ),
        ]
        return custom + urls
    # Add a button/link on the Sessions changelist page
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["sessions_by_user_url"] = reverse(
            f"{self.admin_site.name}:tenant_sessions_by_user"
        )
        return super().changelist_view(request, extra_context=extra_context)

    def sessions_by_user_view(self, request):
        now = timezone.now()
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise PermissionDenied("No tenant")

        tenant_user_ids = _tenant_user_ids(request)
       
        counts = defaultdict(int)
        last_expiry = {}

        for s in Session.objects.filter(expire_date__gt=now).only("session_data", "expire_date"):
            uid = _session_user_id(s)
            if uid is None or uid not in tenant_user_ids:
                continue
            counts[uid] += 1
            if uid not in last_expiry or s.expire_date > last_expiry[uid]:
                last_expiry[uid] = s.expire_date

        users = (
            CustomUser.objects.filter(id__in=list(counts.keys()))
            .order_by("email")
        )

        rows = []
        for u in users:
            rows.append({
                "user": u,
                "count": counts.get(u.id, 0),
                "last_expiry": last_expiry.get(u.id),
                "view_url": reverse(
                    f"{self.admin_site.name}:tenant_sessions_for_user",
                    args=[u.id],
                ),
                "revoke_url": reverse(
                    f"{self.admin_site.name}:tenant_revoke_user_sessions",
                    args=[u.id],
                ),
            })

        context = {
            **self.admin_site.each_context(request),
            "title": "Active sessions (by user)",
            "rows": rows,
            "back_url": reverse(f"{self.admin_site.name}:sessions_session_changelist"),
        }
        return render(request, "admin/sessions/session/by_user.html", context)

    def sessions_for_user_view(self, request, user_id: int):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise PermissionDenied("No tenant")

        user = get_object_or_404(CustomUser, pk=user_id, tenant=tenant, is_platform_admin=False)

       
        now = timezone.now()
        sessions = []
        for s in Session.objects.filter(expire_date__gt=now).order_by("-expire_date"):
            if _session_user_id(s) == user.id:
                sessions.append(s)

        context = {
            **self.admin_site.each_context(request),
            "title": f"Active sessions for {user.email}",
            "target_user": user,
            "sessions": sessions,
            "revoke_url": reverse(
                f"{self.admin_site.name}:tenant_revoke_user_sessions",
                args=[user.id],
            ),
            "back_url": reverse(f"{self.admin_site.name}:tenant_sessions_by_user"),
        }
        return render(request, "admin/sessions/session/user_sessions.html", context)

    def revoke_user_sessions_view(self, request, user_id: int):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise PermissionDenied("No tenant")

        user = get_object_or_404(CustomUser, pk=user_id, tenant=tenant, is_platform_admin=False)

        now = timezone.now()
        deleted = 0
        for s in Session.objects.filter(expire_date__gt=now):
            if _session_user_id(s) == user.id:
                s.delete()
                deleted += 1

        messages.success(request, f"Revoked {deleted} session(s) for {user.email}.")
        return redirect(reverse(f"{self.admin_site.name}:tenant_sessions_for_user", args=[user.id]))


#tenant_admin_site.register(AuditLog, AuditLogAdmin)
tenant_admin_site.register(CustomUser, TenantUserAdmin)
tenant_admin_site.register(TenantRolePermission, TenantRolePermissionTenantAdmin)
tenant_admin_site.register(Session, SessionAdmin)