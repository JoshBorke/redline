from django import forms
from django.template.defaultfilters import slugify
from redline.accounts.models import Account, AccountType


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('account_type', 'name', 'description', 'website', 'due')

    def save(self):
        if not self.instance.slug:
            self.instance.slug = slugify(self.cleaned_data['name'])
        super(AccountForm, self).save()


class AccountTypeForm(forms.ModelForm):
    class Meta:
        model = AccountType
        fields = ('name')

    def save(self):
        if not self.instance.slug:
            self.instance.slug = slugify(self.cleaned_data['name'])
        super(AccountTypeForm, self).save()


CHOICES = (
    ('csv', 'CSV'),
    ('ofx', 'OFX'),
)

class UploadFileForm(forms.Form):
    file = forms.FileField()
    type = forms.ChoiceField(CHOICES)
