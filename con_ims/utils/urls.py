from django.urls import path
from utils import views

urlpatterns = [
    # home pages
    path("", views.landing_page, name="landing_page"),
    path("portal/", views.portal_page, name="portal_page"),

    # Membership
    path("memberships/", views.membership_list, name="membership_list"),
    path("memberships/create/", views.membership_create, name="membership_create"),
    path("memberships/<int:pk>/edit/", views.membership_update, name="membership_update"),
    path("memberships/<int:pk>/delete/", views.membership_delete, name="membership_delete"),
]
