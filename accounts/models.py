from django.db import models
from redline.categories.models import StandardMetadata, ActiveManager
import datetime

class AccountType(StandardMetadata):
    """
    AccountType is the type of account
    """
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name_plural = 'Account Types'
    def __unicode__(self):
        return self.name

class Account(StandardMetadata):
    """
    Accounts are where all transactions must be stored.
    """
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255)
    account_type = models.ForeignKey(AccountType)
    due = models.DateField()
    #website = models.URLField()

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name_plural = 'Accounts'

    def __unicode__(self):
        return u"%s (%s) - %s" % (self.name, self.account_type, self.description)

    def get_income(self):
        from transactions.models import Transaction
        income = 0
        for transaction in Transaction.objects.filter(account=self).filter(transaction_type='income'):
            income += float(transaction.amount)
        return income

    def get_expense(self):
        from transactions.models import Transaction
        expense = 0
        for transaction in Transaction.objects.filter(account=self).filter(transaction_type='expense'):
            expense += float(transaction.amount)
        return expense

    def get_income_by_month(self, year, month):
        from transactions.models import Transaction
        income = 0
        tStart = date(year, month, 1)
        tEnd = date(year, month + 1, 1)
        for transaction in Transaction.objects.filter(
                                            account=self
                                        ).filter(
                                            transaction_type='income'
                                        ).exclude(
                                            date__gte=tEnd # except before tEnd
                                        ).filter(
                                            date__gte=tStart # filtered after tStart
                                        ):
            income += float(transaction.amount)
        return income

    def get_expense_by_month(self, year, month):
        from transactions.models import Transaction
        expense = 0
        tStart = date(year, month, 1)
        tEnd = date(year, month + 1, 1)
        for transaction in Transaction.objects.filter(
                                            account=self
                                        ).filter(
                                            transaction_type='expense'
                                        ).exclude(
                                            date__gte=tEnd # except before tEnd
                                        ).filter(
                                            date__gte=tStart # filtered after tStart
                                        ):
            expense += float(transaction.amount)
        return expense

    def get_transactions(self, tStart, tEnd, type):
        from transactions.models import Transaction
        amount = 0
        return Transaction.objects.filter(
                               account=self # filter only transactions on this account
                           ).filter(
                               transaction_type=type # of the specified type
                           ).exclude(
                               date__gte=tEnd # except before tEnd
                           ).filter(
                               date__gte=tStart # filtered after tStart
                           ).exclude(
                               hideFromGraph=True
                           )

    def get_transaction_amounts(self, tStart, tEnd, type):
        from transactions.models import Transaction
        amount = 0
        for trans in self.get_transactions(tStart, tEnd, type):
            amount += trans.amount
        return amount

    def get_transactions_by_cat(self, tStart, tEnd, type, cat):
        from transactions.models import Transaction
        amount = 0
        return Transaction.objects.filter(
                               account=self # filter only transactions on this account
                           ).filter(
                               transaction_type=type # of the specified type
                           ).filter(
                                category=cat
                           ).exclude(
                               date__gte=tEnd # except before tEnd
                           ).filter(
                               date__gte=tStart # filtered after tStart
                           ).exclude(
                               hideFromGraph=True
                           )

    def get_transactions_by_cat_amounts(self, tStart, tEnd, type, cat):
        from transactions.models import Transaction
        amount = 0
        for trans in self.get_transactions_by_cat(tStart, tEnd, type, cat):
            amount += trans.amount
        return amount

    def get_next_due(self):
        from dateutil.rrule import *
        from datetime import *
        rr = rrule(MONTHLY, dtstart=self.due)
        today = datetime.today()
        return rr.after(today).date()
