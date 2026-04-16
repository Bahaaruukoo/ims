from django.urls import path

from . import views

urlpatterns = [
    path("locations/", views.location_list, name="location_list"),
    path("locations/<int:pk>/", views.location_detail, name="location_detail"),
    path("locations/create/", views.location_create, name="location_create"),
    path("locations/<int:pk>/edit/", views.location_update, name="location_update"),
    path("locations/<int:pk>/delete/", views.location_delete, name="location_delete"),

    # Items
    path("items/", views.item_list, name="item_list"),
    path("items/create/", views.item_create, name="item_create"),
    path("items/<int:pk>/edit/", views.item_update, name="item_update"),
    path("items/<int:pk>/delete/", views.item_delete, name="item_delete"),

    # Variants
    path("variants/", views.variant_list, name="variant_list"),
    path("variants/create/", views.variant_create, name="variant_create"),
    path("variants/<int:pk>/edit/", views.variant_update, name="variant_update"),
    path("variants/<int:pk>/delete/", views.variant_delete, name="variant_delete"),

    # Stocks
    path("stocks/", views.stock_list, name="stock_list"),
    path("stocks/create/", views.stock_create, name="stock_create"),
    path("stocks/<int:pk>/edit/", views.stock_update, name="stock_update"),
    path("stocks/<int:pk>/delete/", views.stock_delete, name="stock_delete"),

]
