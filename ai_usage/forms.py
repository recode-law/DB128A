from django import forms
from ai_usage.models import AIFeedback
from django_prose_editor.widgets import ProseEditorWidget


class AIFeedbackForm(forms.ModelForm):
    def __init__(self, *args, **kwargs) -> None:
        court = kwargs.pop("court")
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.initial["court"] = court
        self.initial["user"] = user

    class Meta:
        model = AIFeedback
        fields = ["text", "court", "user", "usage_groups"]
        labels = {
            "text": "Information"
        }
        widgets = {
            "court": forms.HiddenInput(),
            "user": forms.HiddenInput()
        }
