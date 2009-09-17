import re
import datetime
from django.db import models

# Create your models here.
class StandardMetadata(models.Model):
    """
    A basic (abstract) model for metadata.
    """
    created = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(default=datetime.datetime.now)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated = datetime.datetime.now()
        super(StandardMetadata, self).save(*args, **kwargs)

    def delete(self):
        self.is_deleted = True
        self.save()


class ActiveManager(models.Manager):
    def get_query_set(self):
        return super(ActiveManager, self).get_query_set().filter(is_deleted=False)


class Category(StandardMetadata):
    """
    Categories are the means to loosely tie together the transactions and
    budgets.

    They are used to aggregate transactions together and compare them to the
    appropriate budget estimate. For the reasoning behind this, the docstring
    on the Transaction object explains this.
    """
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    hideFromGraph = models.BooleanField(default=False)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name_plural = 'Categories'

    def __unicode__(self):
        return self.name

class CategoryLookup(models.Model):
    """
    This class is used to provide lookups that map transaction notes to categories automatically
    """
    category = models.ForeignKey(Category)
    regex = models.CharField(max_length=64, unique=True)

    def __unicode__(self):
        return str(self.category) + ': ' + self.regex

    def applyToTransactions(self):
        from redline.transactions.models import Transaction
        reg = re.compile(self.regex, re.I)
        for transaction in Transaction.active.all().filter(category=None):
            m = reg.search(str(transaction.notes))
            if m:
                transaction.category = self.category
                transaction.save()

def lookup_category(description):
    """
    This function searches through all the lookups currently defined and
    returns the first matching category for the regex
    """
    lookups = CategoryLookup.objects.all()
    for cat in lookups:
        # ignore case
        regex = re.compile(cat.regex, re.I)
        # search the entire string
        m = regex.search(str(description))
        if m:
            return cat.category
    return None
