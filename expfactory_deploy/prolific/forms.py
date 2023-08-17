
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Field, Layout, Submit, Div
from django.forms import ModelForm
from prolific import models

class SimpleCCForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))

    class Meta:
        model  = models.SimpleCC
        fields = ["completion_url"]