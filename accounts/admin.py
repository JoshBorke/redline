from django.contrib import admin
from redline.accounts.models import AccountType, Account, CheckingAccount, SavingsAccount, LoanAccount, CreditCardAccount

admin.site.register(AccountType)
admin.site.register(Account)
admin.site.register(CheckingAccount)
admin.site.register(SavingsAccount)
admin.site.register(LoanAccount)
admin.site.register(CreditCardAccount)
