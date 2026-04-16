import json

from django import forms


class KeyValueWidget(forms.Widget):
    template_name = "widgets/key_value.html"

    def format_value(self, value):
        if isinstance(value, dict):
            return value
        if not value:
            return {}
        try:
            return json.loads(value)
        except Exception:
            return {}

    def value_from_datadict(self, data, files, name):
        keys = data.getlist(f"{name}_key")
        values = data.getlist(f"{name}_value")

        result = {}
        for k, v in zip(keys, values):
            if k:
                result[k] = v
        return result