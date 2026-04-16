from django import forms
from utils.models import Membership


class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["project", "member", "site", "location"]
        labels = { "location": "Warehouse Location"}
        widgets = {
            "project": forms.Select(attrs={"class": "form-select"}),
            "member": forms.Select(attrs={"class": "form-select"}),
            "site": forms.Select(attrs={"class": "form-select"}),
            "location": forms.Select(attrs={"class": "form-select"}),
        }

