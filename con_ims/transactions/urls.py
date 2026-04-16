from django.urls import path

from . import views

urlpatterns = [
    path("", views.transaction_list_view, name="transaction_list"),
    path("create/", views.TransactionCreateView.as_view(), name="transaction_create"),
    path("<int:pk>/edit/", views.TransactionUpdateView.as_view(), name="transaction_update"),
    path("<int:pk>/delete/", views.TransactionDeleteView.as_view(), name="transaction_delete"),

    path("requests/", views.request_list, name="request_list"),
    path("requests/create/", views.request_create, name="request_create"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("requests/<int:pk>/approve/", views.request_approve, name="request_approve"),

    path("projects/sites/", views.get_sites, name="get_sites"),
    path("projects/stages/", views.get_stages, name="get_stages"),
    path("projects/warehouses/", views.get_warehouses, name="get_warehouses"),

    
    path("store/requests/", views.store_request_list, name="store_request_list"),
    path("store/requests/<int:pk>/", views.store_request_detail, name="store_request_detail"),
    path("store/requests/<int:pk>/approve/", views.store_request_approve, name="store_request_approve"),
    path("store/requests/<int:pk>/reject/", views.store_request_reject, name="store_request_reject"),
    path("store/requests/<int:pk>/dispatch/", views.store_request_dispatch, name="store_request_dispatch"),

    path("incoming/", views.incoming_stock_list, name="incoming_stock_list"),
    path("incoming/create/", views.incoming_stock_create, name="incoming_stock_create"),
    path("incoming/<int:pk>/edit/", views.incoming_stock_update, name="incoming_stock_update"),
    path("incoming/<int:pk>/delete/", views.incoming_stock_delete, name="incoming_stock_delete"),

    path("pending-count/", views.pending_request_count_partial, name="pending_request_count_partial"),

]