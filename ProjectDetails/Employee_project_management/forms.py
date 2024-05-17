from django import forms
class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='Select a Excel file')
