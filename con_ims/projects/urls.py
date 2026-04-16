from django.urls import path

from . import views

urlpatterns = [

    # PROJECT
    path("", views.project_list, name="project_list"),
    path("<int:pk>/", views.project_detail, name="project_detail"),
    path("create/", views.project_create, name="project_create"),
    path("<int:pk>/edit/", views.project_update, name="project_update"),
    path("<int:pk>/delete/", views.project_delete, name="project_delete"),

    # SITE
    path("sites/", views.site_list, name="site_list"),
    path("sites/create/", views.site_create, name="site_create"),
    path("sites/<int:pk>/edit/", views.site_update, name="site_update"),
    path("sites/<int:pk>/delete/", views.site_delete, name="site_delete"),

    # STAGE
    path("stages/", views.stage_list, name="stage_list"),
    path("stages/create/", views.stage_create, name="stage_create"),
    path("stages/<int:pk>/edit/", views.stage_update, name="stage_update"),
    path("stages/<int:pk>/delete/", views.stage_delete, name="stage_delete"),

    # Stage Material (BOQ)
    path("stage-materials/", views.stage_material_list, name="stage_material_list"),
    path("stage-materials/create/", views.stage_material_create, name="stage_material_create"),
    path("stage-materials/<int:pk>/edit/", views.stage_material_update, name="stage_material_update"),
    path("stage-materials/<int:pk>/delete/", views.stage_material_delete, name="stage_material_delete"),

]
