from django.contrib import admin
from redline.accounts.models import AccountType, Account

admin.site.register(AccountType)
admin.site.register(Account)
