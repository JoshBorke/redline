from django import forms
from redline.transactions.models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('transaction_type', 'notes', 'category', 'amount', 'date', 'account', 'hideFromGraph')

