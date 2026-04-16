
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from django.contrib.auth.models import Permission
from django.contrib.auth.views import redirect_to_login
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django_tenants.utils import get_public_schema_name
from psycopg2 import OperationalError, ProgrammingError


class TenantAccessMiddleware:
    """
    Strict tenant boundary enforcement.

    Rules:
    - Platform admins: full access
    - Tenant users: may only access their own tenant domain
    - Tenant users cannot access public admin
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        user = request.user
        tenant = getattr(request, "tenant", None)

        # Not logged in → ignore
        if not user.is_authenticated:
            return self.get_response(request)

        # Platform admins → always allowed
        if getattr(user, "is_platform_admin", False):
            return self.get_response(request)
        '''
        # 🚨 BLOCK tenant users from PUBLIC schema entirely
        if connection.schema_name == get_public_schema_name():
            return HttpResponseForbidden("Tenant users cannot access public area.")
        '''
        # 🚨 STRICT tenant match
        if not tenant or user.tenant_id != tenant.id:
            return HttpResponseForbidden("Cross-tenant access denied.")

        return self.get_response(request)


class PublicAuthSchemaMiddleware(MiddlewareMixin):
    """
    Ensure auth endpoints query users from PUBLIC schema.
    Works well with django-tenants when users live in public schema.
    """

    AUTH_PREFIXES = (
        "/accounts/login/",
        "/admin/login/",
        "/accounts/password/reset/",
        "/accounts/password/change/",
    )

    def process_request(self, request):
        request._schema_before_auth = None
        if request.path.startswith(self.AUTH_PREFIXES):
            request._schema_before_auth = connection.schema_name
            connection.set_schema_to_public()

    def process_response(self, request, response):
        prev = getattr(request, "_schema_before_auth", None)
        if prev and prev != connection.schema_name:
            connection.set_schema(prev)
        return response

    def process_exception(self, request, exception):
        prev = getattr(request, "_schema_before_auth", None)
        if prev:
            connection.set_schema(prev)


class NoTenantUserOnPublicAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            tenant = getattr(request, "tenant", None)
            if tenant is None and request.user.is_authenticated:
                if not getattr(request.user, "is_platform_admin", False):
                    return HttpResponseForbidden("Not allowed.")
        return self.get_response(request)
    

class SessionMetaMiddleware:
    """
    Stores minimal request info into the session so admin can see it.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if getattr(request, "session", None) is not None:
            if request.user and request.user.is_authenticated:
                # Only set if missing, to avoid rewriting session constantly
                if "ip" not in request.session:
                    request.session["ip"] = self._get_ip(request)
                if "ua" not in request.session:
                    request.session["ua"] = request.META.get("HTTP_USER_AGENT", "")[:500]
                request.session["path"] = request.path[:500]

        return response

    def _get_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class RequestLoggingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Default values
        tenant = "anonymous"
        user = "anonymous"

        if hasattr(request, "user") and request.user.is_authenticated:

            user = str(request.user)

            tenant_obj = getattr(request, "tenant", None)
            tenant = str(tenant_obj) if tenant_obj else "public"


        response = self.get_response(request)

        duration = int((time.time() - start_time) * 1000)


        response["X-Request-ID"] = request_id

        return response

