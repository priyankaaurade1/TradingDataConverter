from django import forms
from .models import CSVUpload

class CSVUploadForm(forms.ModelForm):
    timeframe = forms.IntegerField(label='Timeframe (in minutes)', min_value=1)

    class Meta:
        model = CSVUpload
        fields = ['file', 'timeframe']
