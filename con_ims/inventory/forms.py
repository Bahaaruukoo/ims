from django import forms

from .models import ItemVariant, Location, Stock
from .widgets import KeyValueWidget


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["name", "project"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "project": forms.Select(attrs={"class": "form-select"}),
        }

class ItemVariantForm(forms.ModelForm):
    class Meta:
        model = ItemVariant
        fields = "__all__"
        widgets = {
            "attributes": KeyValueWidget(),
        }

from django import forms

from .models import Item, ItemVariant


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["name", "category", "unit"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
        }


class ItemVariantForm(forms.ModelForm):
    class Meta:
        model = ItemVariant
        fields = ["item", "name", "unit_cost", "attributes", "sku"]
        widgets = {
            "item": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "unit_cost": forms.NumberInput(attrs={"class": "form-control"}),
            "attributes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "sku": forms.TextInput(attrs={"class": "form-control"}),
        }

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ["item_variant", "location", "quantity"]
        widgets = {
            "item_variant": forms.Select(attrs={"class": "form-select"}),
            "location": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }
    def validate_unique(self):
        # Disable model-level unique checks
        pass

    def clean(self):
        cleaned_data = super().clean()

        # Remove NON-FIELD ERRORS added by unique_together
        if "__all__" in self._errors:
            del self._errors["__all__"]

        return cleaned_data

