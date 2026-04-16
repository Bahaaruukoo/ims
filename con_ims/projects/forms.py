from django import forms

from .models import Project, ProjectStage, Site, StageMaterial


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "start_date", "end_date", "status"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ["project", "name", "description"]
        widgets = {
            "project": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ProjectStageForm(forms.ModelForm):
    class Meta:
        model = ProjectStage
        fields = ["project", "site", "name", "order", "start_date", "end_date", "status"]
        widgets = {
            "project": forms.Select(attrs={"class": "form-select"}),
            "site": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

class StageMaterialForm(forms.ModelForm):
    class Meta:
        model = StageMaterial
        fields = ["stage", "item_variant", "planned_quantity"]
        widgets = {
            "stage": forms.Select(attrs={"class": "form-select"}),
            "item_variant": forms.Select(attrs={"class": "form-select"}),
            "planned_quantity": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

