from django import forms


class SearchTickerForm(forms.Form):
    ticker = forms.CharField(required=True, max_length=5, widget=forms.TextInput(attrs={'placeholder': 'Search'}))
