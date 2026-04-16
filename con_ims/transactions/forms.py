from django import forms
from inventory.models import ItemVariant, Location
from projects.models import Project

from .models import IncomingStock


class IncomingStockForm(forms.ModelForm):
    class Meta:
        model = IncomingStock
        fields = [
            "item_variant",
            "quantity",
            "location",
            "project",
            "driver",
            "vehicle_number",
        ]
        widgets = {
            "item_variant": forms.Select(attrs={"class": "form-select"}),
            "location": forms.Select(attrs={"class": "form-select"}),
            "project": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "driver": forms.TextInput(attrs={"class": "form-control"}),
            "vehicle_number": forms.TextInput(attrs={"class": "form-control"}),
        }
