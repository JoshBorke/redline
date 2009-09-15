from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from csv import DictReader
from redline.accounts.models import Account, AccountType
from redline.accounts.forms import AccountForm, AccountTypeForm, UploadFileForm
from redline.transactions.models import Transaction
from redline.categories.models import CategoryLookup, Category, lookup_category
import redline.categories.models
from dateutil.parser import *
from datetime import date,datetime
from redline.ofc2 import *

# Create your views here.
#def account_import(request, account_id):
def import_transaction(account_id, row):
    account = Account.objects.get(id=account_id)
    map = None
    cat = None
    if (account.name == 'Checking' and str(account.account_type.slug) == 'checking'):
        map = {'notes':'Description', 'date':'Date'}
        if (row['Credit'] == ''):
            row['Credit'] = 0
        if (row['Debit'] == ''):
            row['Debit'] = 0
        if (float(row['Credit']) > 0):
            map['type'] = 'income'
            map['amount'] = row['Credit']
        else:
            map['type'] = 'expense'
            map['amount'] = row['Debit']
    elif ((str(account.name) == 'Credit Card' and str(account.account_type.slug) == 'credit_card') or
         (str(account.name) == 'Debit Card' and str(account.account_type.slug) == 'credit_card')):
        # all transactions on a credit card are expenses
        map = {'notes':'Description', 'date':'Date', 'type':'expense'}
        if row['Credit']:
            row['Credit'] = row['Credit'].replace(',','')
            row['Credit'] = row['Credit'].replace('$','')
            if (row['Credit'].strip(' ') == ''):
                row['Credit'] = 0
        else:
            row['Credit'] = 0
        if row['Debit']:
            row['Debit'] = row['Debit'].replace(',','')
            row['Debit'] = row['Debit'].replace('$','')
            row['Debit'].strip(' ')
            if (row['Debit'] == ''):
                row['Debit'] = 0
        else:
            row['Debit'] = 0
        if (float(row['Credit']) > 0):
            map['type'] = 'income'
            map['amount'] = row['Credit']
        else:
            map['amount'] = row['Debit']
    else:
        return None
    if map:
        cat = lookup_category(row[map['notes']])
    try:
        dupe_in_db = Transaction.objects.get(account = account,
                                             notes = row[map['notes']],
                                             date = parse(row[map['date']]),
                                             amount = map['amount'],
                                             transaction_type = map['type'])
    except ObjectDoesNotExist:
        transaction = Transaction(account = account,
                                  notes = row[map['notes']],
                                  date = parse(row[map['date']]),
                                  amount = map['amount'],
                                  transaction_type = map['type'])
        transaction.amount = map['amount']
        if (cat != None):
            transaction.category = cat
            transaction.hideFromGraph = cat.hideFromGraph
        transaction.save()
        return True
    return False

def parse_ofx_file(f, account_id):
    import re
    account = Account.objects.get(id=account_id)
    found = False
    start = re.compile("<OFX>")
    end = re.compile("</OFX>")
    lineItem = re.compile("<([A-Z]+)>(.+)")
    transTag = re.compile(".*STMTTRN>")
    inTrans = False
    res = ""
    transactions = []
    trans = None
    lines = []
    lines.append("<html>")
    for line in f:
        if start.match(line):
            found = True
        if found:
            if transTag.match(line):
                inTrans = not inTrans
                if inTrans:
                    trans = {}
                    continue
                else:
                    transactions.append(trans)
                    continue
        if inTrans:
            line = line.strip()
            results = lineItem.match(line)
            if results:
                tag = results.group(1)
                item = results.group(2)
                #print("Line: %s\nTag: %s:\t%s" % (line, tag, item))
                trans[tag] = item
        if end.match(line):
            found = False

    for trans in transactions:
        datestr = trans['DTPOSTED']
        year = int(datestr[0:4])
        month = int(datestr[4:6])
        day = int(datestr[6:8])
        hour = int(datestr[8:10])
        minute = int(datestr[10:12])
        second = int(datestr[12:14])
        if (second >= 60):
            minute += 1
            second = 0
        trans['DTPOSTED'] = datetime(year, month, day, hour, minute, second)
        # make the transaction amount always positive, should this always be
        # the case?
        trans['TRNAMT'] = str(abs(float(trans['TRNAMT'])))
        if trans['TRNTYPE'] == 'DEBIT':
            type = 'expense'
        elif trans['TRNTYPE'] == 'CREDIT':
            type = 'income'
        try:
            dupe_in_db = Transaction.objects.get(account = account,
                                                 notes = trans['NAME'],
                                                 date = trans['DTPOSTED'],
                                                 amount = trans['TRNAMT'],
                                                 fitid = trans['FITID'],
                                                 transaction_type = type)
            lines.append("Transaction already exists<br/>")
        except ObjectDoesNotExist:
            transaction = Transaction(account = account,
                                      notes = trans['NAME'],
                                      date = trans['DTPOSTED'],
                                      amount = trans['TRNAMT'],
                                      fitid = trans['FITID'],
                                      transaction_type = type)
            cat = lookup_category(trans['NAME'])
            if (cat != None):
                transaction.category = cat
                transaction.hideFromGraph = cat.hideFromGraph
            transaction.save()
            lines.append("Imported a new transaction<br/>")
    lines.append("</html>")
    return '\n'.join(lines)

def handle_uploaded_file(file, account_id):
    lines = []
    reader = DictReader(file)
    account = Account.objects.get(id=account_id)
    lines.append(account.name)
    lines.append(account.slug)
    lines.append(str(account.account_type))
    imported = 0
    # for each transaction in the file
    for row in reader:
        ret = import_transaction(account_id, row)
        if (ret == None):
            lines.append('<br/>')
            lines.append(str(row))
        elif (ret == False):
            lines.append('Already imported ' + str(row))
            lines.append('<br/>')
        else:
            imported += 1

    lines.append('<br/>')
    lines.append("Imported " + str(imported) + " transactions")
    return '\n'.join(lines)

def parse_upload(type, file, account_id):
    if type == 'csv':
        return handle_uploaded_file(file, account_id)
    elif type == 'ofx':
        return parse_ofx_file(file, account_id)

def account_import(request, account_id):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            type = form.cleaned_data['type']
            return render_to_response(
                    'accounts/upload.html',
                    {'info': parse_upload(type, request.FILES['file'], account_id)}
            )
            #return HttpResponse(parse_ofx_file(request.FILES['file'], account_id))
    else:
        form = UploadFileForm()
    return render_to_response('accounts/upload.html', {'form': form})

def account_list(request, model_class=Account, template_name='accounts/list.html'):
    """
    A list of account_type objects.

    Templates: ``accounts/list.html``
    Context:
        account_types
            paginated list of account_type objects
        paginator
            A Django Paginator instance
        page
            current page of account_type objects
    """
    account_list = model_class.active.all()
    today = date.today()
    year = today.year
    income = line()
    mydot = dot()
    mydot.dot_size = 5
    mydot.style = 'hollow'
    mydot.halosize = 5
    mydot.on_click = "monthClicked"
    income.width = 2
    income.color = "00FF00"
    v = []
    t = []
    for month in range(1, 11):
        amount = 0
        tStart = date(year, month, 1)
        tEnd = date(year, month + 1, 1)
        for account in account_list:
            for transaction in account.get_transactions(tStart, tEnd, 'income'):
                amount += transaction.amount
        v.append(float(amount))
        t.append(float(amount))
    tStart = date(year, 12, 1)
    tEnd = date(year + 1, 1, 1)
    amount = 0
    for account in account_list:
        for transaction in account.get_transactions(tStart, tEnd, 'income'):
            amount += transaction.amount
    v.append(float(amount))
    t.append(float(amount))
    income.values = v
    income.dot_style = mydot
    income.dot_size = mydot
    expense = line()
    expense.dot_style = mydot
    expense.dot_size = mydot
    expense.width = 2
    expense.color = "FF0000"
    v = []
    for month in range(1, 11):
        amount = 0
        tStart = date(year, month, 1)
        tEnd = date(year, month + 1, 1)
        for account in account_list:
            for transaction in account.get_transactions(tStart, tEnd, 'expense'):
                amount += transaction.amount
        v.append(float(amount))
        t.append(float(amount))
    tStart = date(year, 12, 1)
    tEnd = date(year + 1, 1, 1)
    amount = 0
    for account in account_list:
        for transaction in account.get_transactions(tStart, tEnd, 'expense'):
            amount += transaction.amount
    v.append(float(amount))
    t.append(float(amount))
    expense.values = v
    x = x_axis()
    x.min, x.max, x.steps = 1, 12, 1
    labels = x_axis_labels()
    labels.labels = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    x.labels = labels
    y = y_axis()
    y.min, y.max = 0, max(t)
    chart = open_flash_chart()
    chart.title = title(text="All accounts")
    chart.add_element(income)
    chart.add_element(expense)
    chart.x_axis = x
    chart.y_axis = y
    return render_to_response(template_name, {
        'accounts': account_list,
        'year': year,
        'chart_data': str(chart),
    }, context_instance=RequestContext(request))

def account_info(request, account_id, model_class=Account, template_name='accounts/list.html'):
    """
    The account information page displays a graph with the transactions for an
        entire year
    """
    account = get_object_or_404(model_class.active.all(), pk=account_id)
    today = date.today()
    year = today.year
    income = line()
    mydot = dot()
    mydot.dot_size = 5
    mydot.style = 'hollow'
    mydot.halosize = 5
    mydot.on_click = "monthClicked"
    income.width = 2
    income.color = "00FF00"
    v = []
    transactions = []
    maxAmount = 0
    for month in range(1, 11):
        tStart = date(year, month, 1)
        tEnd = date(year, month + 1, 1)
        amount = account.get_transaction_amounts(tStart, tEnd, 'income')
        transactions.extend(account.get_transactions(tStart, tEnd, 'income'))
        v.append(float(amount))
        maxAmount = max(maxAmount, amount)
    tStart = date(year, 12, 1)
    tEnd = date(year + 1, 1, 1)
    amount = account.get_transaction_amounts(tStart, tEnd, 'income')
    transactions.extend(account.get_transactions(tStart, tEnd, 'income'))
    maxAmount = max(maxAmount, amount)
    v.append(float(amount))
    income.values = v
    income.dot_style = mydot
    income.dot_size = mydot
    expense = line()
    expense.dot_style = mydot
    expense.dot_size = mydot
    expense.width = 2
    expense.color = "FF0000"
    v = []
    for month in range(1, 11):
        amount = 0
        tStart = date(year, month, 1)
        tEnd = date(year, month + 1, 1)
        amount = account.get_transaction_amounts(tStart, tEnd, 'expense')
        transactions.extend(account.get_transactions(tStart, tEnd, 'expense'))
        maxAmount = max(maxAmount, amount)
        v.append(float(amount))
    tStart = date(year, 12, 1)
    tEnd = date(year + 1, 1, 1)
    amount = account.get_transaction_amounts(tStart, tEnd, 'expense')
    maxAmount = max(maxAmount, amount)
    transactions.extend(account.get_transactions(tStart, tEnd, 'expense'))
    v.append(float(amount))
    expense.values = v
    x = x_axis()
    x.min, x.max, x.steps = 1, 12, 1
    labels = x_axis_labels()
    labels.labels = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    x.labels = labels
    y = y_axis()
    y.min, y.max = 0, float(maxAmount)
    chart = open_flash_chart()
    chart.title = title(text=str(account.name))
    chart.add_element(income)
    chart.add_element(expense)
    chart.x_axis = x
    chart.y_axis = y
    return render_to_response(template_name, {
        'account': account,
        'chart_data': str(chart),
        'year': year,
        'transactions': transactions,
    }, context_instance=RequestContext(request))

# todo: make this barstack
def accounts_detail(request, month, year, model_class=Account, template_name='accounts/list.html'):
    """
    The account information page displays a graph with the transactions for an
        entire year
    """
    account_list = model_class.active.all()
    details = bar()
    details.on_click = 'typeClicked'
    maxAmount = 0
    v = []
    transactions = []
    amount = 0
    tStart = date(int(year), int(month), 1)
    tEnd = date(int(year), int(month) + 1, 1)
    for account in account_list:
        amount += account.get_transaction_amounts(tStart, tEnd, 'income')
        transactions.extend(account.get_transactions(tStart, tEnd, 'income'))
    value = barvalue()
    value.colour = "#00FF00"
    value.top = float(amount)
    maxAmount = amount
    v.append(value)
    amount = 0
    for account in account_list:
        amount += account.get_transaction_amounts(tStart, tEnd, 'expense')
        transactions.extend(account.get_transactions(tStart, tEnd, 'expense'))
    value = barvalue()
    value.colour = "#FF0000"
    value.top = float(amount)
    maxAmount = max(maxAmount, amount)
    v.append(value)
    details.values = v
    x = x_axis()
    labels = x_axis_labels()
    labels.labels = ["Income", "Expenses"]
    x.labels = labels
    y = y_axis()
    y.min, y.max = 0, float(maxAmount)
    chart = open_flash_chart()
    chart.title = title(text="Detail for " + month + "/" + year)
    chart.add_element(details)
    chart.x_axis = x
    chart.y_axis = y
    return render_to_response(template_name, {
        'transactions': transactions,
        'chart_data': str(chart),
        'year': year,
        'month': month,
    }, context_instance=RequestContext(request))

def account_detail(request, account_id, month, year, model_class=Account, template_name='accounts/detail.html'):
    """
    The account information page displays a graph with the transactions for an
        entire year
    """
    account = get_object_or_404(model_class.active.all(), pk=account_id)
    details = bar()
    details.on_click = 'on_click'
    v = []
    transactions = []
    tStart = date(int(year), int(month), 1)
    tEnd = date(int(year), int(month) + 1, 1)
    amount = account.get_transaction_amounts(tStart, tEnd, 'income')
    transactions.extend(account.get_transaction(tStart, tEnd, 'income'))
    value = barvalue()
    value.colour = "#00FF00"
    value.top = float(amount)
    v.append(value)
    maxAmount = amount
    amount = 0
    amount = account.get_transaction_amounts(tStart, tEnd, 'expense')
    transactions.extend(account.get_transaction(tStart, tEnd, 'expense'))
    value = barvalue()
    value.colour = "#FF0000"
    value.top = float(amount)
    v.append(value)
    maxAmount = max(maxAmount, amount)
    details.values = v
    x = x_axis()
    labels = x_axis_labels()
    labels.labels = ["Income", "Expenses"]
    x.labels = labels
    y = y_axis()
    y.min, y.max = 0, float(maxAmount)
    chart = open_flash_chart()
    chart.title = title(text=str(account.name))
    chart.add_element(details)
    chart.x_axis = x
    chart.y_axis = y
    return render_to_response(template_name, {
        'account': account,
        'chart_data': str(chart),
        'year': year,
        'month': month,
        'transactions': transactions,
    }, context_instance=RequestContext(request))

def accounts_detail_type(request, month, year, ttype, model_class=Account, template_name='accounts/list.html'):
    """
    The account information page displays a graph with the transactions for an
        entire year
    """
    accounts = model_class.active.all()
    details = pie()
    colours = ["FF3399", "FF9900", "00FF00", "0000FF", "FF000", "990099", "FFFF33"]
    details.colours = colours
    v = []
    transactions = []
    tStart = date(int(year), int(month), 1)
    tEnd = date(int(year), int(month) + 1, 1)
    if (int(ttype) == 0):
        ttype = "income"
    else:
        ttype = "expense"
    for cat in Category.active.all():
        if (not cat.hideFromGraph):
            amount = 0
            for account in accounts:
                for transaction in account.get_transactions_by_cat(tStart, tEnd, ttype, cat):
                    amount += transaction.amount
                    transactions.append(transaction)
            value = pie_value(value=float(amount))
            value.tip = str(cat) + ': $#val#'
            value.label = str(cat)
            value.amount = float(amount)
            v.append(value)
    amount = 0
    for account in accounts:
        for transaction in account.get_transactions(tStart, tEnd, ttype):
            if (transaction.category == None):
                amount += transaction.amount
                transactions.append(transaction)
    value = pie_value(value=float(amount))
    value.tip = 'Misc: $#val#'
    value.amount = float(amount)
    v.append(value)
    details.values = v
    chart = open_flash_chart()
    chart.title = title(text=ttype + " Detail for " + month + "/" + year)
    chart.add_element(details)
    return render_to_response(template_name, {
        'account': account,
        'chart_data': str(chart),
        'month': month,
        'year': year,
        'type': ttype,
        'transactions': transactions,
    }, context_instance=RequestContext(request))

def account_detail_type(request, account_id, month, year, ttype, model_class=Account, template_name='accounts/detail.html'):
    """
    The account information page displays a graph with the transactions for an
        entire year
    """
    account = get_object_or_404(model_class.active.all(), pk=account_id)
    details = pie()
    colours = ["FF3399", "FF9900", "00FF00", "0000FF", "FF000", "990099", "FFFF33"]
    details.colours = colours
    v = []
    transactions = []
    tStart = date(int(year), int(month), 1)
    tEnd = date(int(year), int(month) + 1, 1)
    if (int(ttype) == 0):
        ttype = "income"
    else:
        ttype = "expense"
    for cat in Category.active.all():
        if (not cat.hideFromGraph):
            amount = account.get_transactions_by_cat_amounts(tStart, tEnd, ttype, cat)
            transactions.extend(account.get_transactions_by_cat(tStart, tEnd, ttype, cat))
            value = pie_value(value=float(amount))
            value.tip = str(cat) + ': $#val#'
            value.label = str(cat)
            value.amount = float(amount)
            v.append(value)
    #amount = account.get_transactions_by_cat_amounts(tStart, tEnd, ttype, None)
    amount = 0
    for transaction in account.get_transactions(tStart, tEnd, ttype):
        if (transaction.category == None):
            amount += transaction.amount
            transactions.append(transaction)
    value = pie_value(value=float(amount))
    value.tip = 'Misc: $#val#'
    value.amount = float(amount)
    v.append(value)
    details.values = v
    chart = open_flash_chart()
    chart.title = title(text=str(account.name))
    chart.add_element(details)
    return render_to_response(template_name, {
        'account': account,
        'chart_data': str(chart),
        'month': month,
        'year': year,
        'transactions': transactions,
    }, context_instance=RequestContext(request))

def account_add(request, form_class=AccountForm, template_name='accounts/add.html'):
    """
    Create a new account_type object.

    Templates: ``accounts/add.html``
    Context:
        form
            a account_type form
    """
    if request.POST:
        form = form_class(request.POST)

        if form.is_valid():
            account = form.save()
            return HttpResponseRedirect(reverse('account_list'))
    else:
        form = form_class()
    return render_to_response(template_name, {
        'form': form,
    }, context_instance=RequestContext(request))

def account_edit(request, account_id, model_class=Account, form_class=AccountForm, template_name='accounts/edit.html'):
    """
    Edit a account_type object.

    Templates: ``accounts/edit.html``
    Context:
        account_type
            the existing account_type object
        form
            a account_type form
    """
    account = get_object_or_404(model_class.active.all(), pk=account_id)
    if request.POST:
        form = form_class(request.POST, instance=account)

        if form.is_valid():
            category = form.save()
            return HttpResponseRedirect(reverse('account_list'))
    else:
        form = form_class(instance=account)
    return render_to_response(template_name, {
        'account': account,
        'form': form,
    }, context_instance=RequestContext(request))

def account_delete(request, account_id, model_class=Account, template_name='accounts/delete.html'):
    """
    Delete a account_type object.

    Templates: ``accounts/delete.html``
    Context:
        account_type
            the existing account_type object
    """
    account_type = get_object_or_404(Account.active.all(), pk=account_id)
    if request.POST:
        if request.POST.get('confirmed'):
            account_type.delete()
        return HttpResponseRedirect(reverse('account_list'))
    return render_to_response(template_name, {
        'account_type': account_type,
    }, context_instance=RequestContext(request))

def account_type_list(request, model_class=AccountForm, template_name='accounts/list.html'):
    """
    A list of account_type objects.

    Templates: ``accounts/list.html``
    Context:
        account_types
            paginated list of account_type objects
        paginator
            A Django Paginator instance
        page
            current page of account_type objects
    """
    account_type_list = model_class.active.order_by('-date', '-created')
    try:
        paginator = Paginator(account_type_list, getattr(settings, 'BUDGET_LIST_PER_PAGE', 50))
        page = paginator.page(request.GET.get('page', 1))
        account_types = page.object_list
    except InvalidPage:
        raise Http404('Invalid page requested.')
    return render_to_response(template_name, {
        'account_types': account_types,
        'paginator': paginator,
        'page': page,
    }, context_instance=RequestContext(request))

def account_type_add(request, form_class=AccountTypeForm, template_name='accounts/add.html'):
    """
    Create a new account_type object.

    Templates: ``accounts/add.html``
    Context:
        form
            a account_type form
    """
    if request.POST:
        form = form_class(request.POST)

        if form.is_valid():
            account_type = form.save()
            return HttpResponseRedirect(reverse('account_type_list'))
    else:
        form = form_class()
    return render_to_response(template_name, {
        'form': form,
    }, context_instance=RequestContext(request))

def account_type_edit(request, account_type_id, model_class=AccountType, form_class=AccountTypeForm, template_name='accounts/edit.html'):
    """
    Edit a account_type object.

    Templates: ``accounts/edit.html``
    Context:
        account_type
            the existing account_type object
        form
            a account_type form
    """
    account_type = get_object_or_404(model_class.active.all(), pk=account_type_id)
    if request.POST:
        form = form_class(request.POST, instance=account_type)

        if form.is_valid():
            category = form.save()
            return HttpResponseRedirect(reverse('account_type_list'))
    else:
        form = form_class(instance=account_type)
    return render_to_response(template_name, {
        'account_type': account_type,
        'form': form,
    }, context_instance=RequestContext(request))

def account_type_delete(request, account_type_id, model_class=AccountType, template_name='accounts/delete.html'):
    """
    Delete a account_type object.

    Templates: ``accounts/delete.html``
    Context:
        account_type
            the existing account_type object
    """
    account_type = get_object_or_404(AccountType.active.all(), pk=account_type_id)
    if request.POST:
        if request.POST.get('confirmed'):
            account_type.delete()
        return HttpResponseRedirect(reverse('account_type_list'))
    return render_to_response(template_name, {
        'account_type': account_type,
    }, context_instance=RequestContext(request))
