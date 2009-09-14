from django import forms
from django.template.defaultfilters import slugify
from redline.categories.models import Category, CategoryLookup

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name','hideFromGraph')

    def save(self):
        if not self.instance.slug:
            self.instance.slug = slugify(self.cleaned_data['name'])
        super(CategoryForm, self).save()

class CategoryLookupForm(forms.ModelForm):
    class Meta:
        model = CategoryLookup
        fields = ('category','regex')
