from django.urls import path

from .views import project_dashboard

urlpatterns = [
    path("project/consumption/", project_dashboard, name="consumption_chart"),
]