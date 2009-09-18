from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from redline.categories.models import *
from redline.transactions.models import Transaction
from redline.transactions.forms import TransactionForm

def transaction_list(request, model_class=Transaction, template_name='transactions/list.html'):
    """
    A list of transaction objects.

    Templates: ``transactions/list.html``
    Context:
        transactions
            paginated list of transaction objects
        paginator
            A Django Paginator instance
        page
            current page of transaction objects
    """
    transaction_list = model_class.active.order_by('-date', '-created')
    return render_to_response(template_name, {
        'transactions': transaction_list,
    }, context_instance=RequestContext(request))


def transaction_add(request, form_class=TransactionForm, template_name='transactions/add.html'):
    """
    Create a new transaction object.

    Templates: ``transactions/add.html``
    Context:
        form
            a transaction form
    """
    if request.POST:
        form = form_class(request.POST)

        if form.is_valid():
            transaction = form.save()
            return HttpResponseRedirect(reverse('redline_transaction_list'))
    else:
        form = form_class()
    return render_to_response(template_name, {
        'form': form,
    }, context_instance=RequestContext(request))


def transaction_edit(request, transaction_id, model_class=Transaction, form_class=TransactionForm, template_name='transactions/edit.html'):
    """
    Edit a transaction object.

    Templates: ``transactions/edit.html``
    Context:
        transaction
            the existing transaction object
        form
            a transaction form
    """
    transaction = get_object_or_404(model_class.active.all(), pk=transaction_id)
    if request.POST:
        form = form_class(request.POST, instance=transaction)

        if form.is_valid():
            transaction = form.save()
            return HttpResponseRedirect(reverse('redline_transaction_list'))
    else:
        form = form_class(instance=transaction)
    return render_to_response(template_name, {
        'transaction': transaction,
        'form': form,
    }, context_instance=RequestContext(request))

def transaction_ajax_edit_amount(request, model_class=Transaction):
    """
    Edits a transaction object from an ajax call.
    """
    if request.POST:
        id = request.POST.get('id')
        value = request.POST.get('value')
        transaction_id, _, field = id.partition('-')
        transaction = get_object_or_404(model_class.active.all(), pk=transaction_id)
        transaction.amount = value
        transaction.save()
        return HttpResponse('$' + str(value))

def transaction_ajax_edit_type(request, model_class=Transaction):
    """
    Edits a transaction object from an ajax call.
    """
    if request.POST:
        id = request.POST.get('id')
        value = request.POST.get('value')
        transaction_id, _, field = id.partition('-')
        transaction = get_object_or_404(model_class.active.all(), pk=transaction_id)
        transaction.transaction_type = value
        transaction.save()
        return HttpResponse(transaction.transaction_type)

def transaction_ajax_edit_category(request, model_class=Transaction):
    """
    Edits a transaction object from an ajax call.
    """
    if request.POST:
        id = request.POST.get('id')
        value = request.POST.get('value')
        transaction = get_object_or_404(model_class.active.all(), pk=id)
        cat = get_object_or_404(Category.active.all(), slug=value)
        transaction.category = cat
        transaction.save()
        return HttpResponse(cat.name)


def transaction_delete(request, transaction_id, model_class=Transaction, template_name='transactions/delete.html'):
    """
    Delete a transaction object.

    Templates: ``transactions/delete.html``
    Context:
        transaction
            the existing transaction object
    """
    transaction = get_object_or_404(Transaction.active.all(), pk=transaction_id)
    if request.POST:
        if request.POST.get('confirmed'):
            transaction.delete()
        return HttpResponseRedirect(reverse('redline_transaction_list'))
    return render_to_response(template_name, {
        'transaction': transaction,
    }, context_instance=RequestContext(request))

def chart(request):

    return render_to_response('site_media/charts/chart.html', {
        'var': 'var',
    }, context_instance=RequestContext(request) )

def data_overview(request):
    """
    Returns the overview of all transactions
    Context:
    """
    plot = Pie(start_angle = 35, animate = True)
    plot.set_tooltip("#val# of #total#<br>#percent# of 100%")
    plot.set_gradient_fill(True)
    income = 0
    expense = 0
    for transaction in Transaction.objects.filter(transaction_type='income'):
        income += float(transaction.amount)
    for transaction in Transaction.objects.filter(transaction_type='expense'):
        expense += float(transaction.amount)
    piece = pie_value(income, tooltip="Income")
    piece.set_on_click('http://localhost:8000/data/transactions/income/')
    plot.append_values(piece)
    piece = pie_value(expense, tooltip="Expense")
    piece.set_on_click('http://localhost:8000/data/transactions/expense/')
    plot.append_values(piece)
    #plot.append_values(pie_value(expense, ("Expense", '#FF33C9')))
    #plot.append_values(pie_value(expense, tooltip="Expense", label="Expense"))
    chart = openFlashChart.template("All Transactions")
    chart.add_element(plot)
    return render_to_response('chart.html', {
        'chart_data': chart.encode(),
    }, context_instance=RequestContext(request))
    #return HttpResponse(chart.encode())

def data_expense_or_income(request, t_type):
    """
    Returns the overview of all transactions of the specified type
    Context:
    """
    plot = Pie(start_angle = 35, animate = True)
    plot.set_tooltip("#val# of #total#<br>#percent# of 100%")
    plot.set_gradient_fill(True)
    for cat in Category.objects.all():
        aggregate = 0
        for transaction in Transaction.objects.filter(transaction_type=t_type).filter(category=cat):
            aggregate += float(transaction.amount)
        if (aggregate != 0):
            plot.append_values(aggregate)
    chart = openFlashChart.template("Transactions" + t_type + "")
    chart.add_element(plot)
    return render_to_response('chart.html', {
        'chart_data': chart.encode(),
    }, context_instance=RequestContext(request))
    #return HttpResponse(chart.encode())

def chart_test(request):
    plot = Pie(start_angle = 35, animate = True)
    plot.set_tooltip("#val# of #total#<br>#percent# of 100%")
    plot.set_gradient_fill(True)
    income = 0
    expense = 0
    for transaction in Transaction.objects.filter(transaction_type='income'):
        income += float(transaction.amount)
    for transaction in Transaction.objects.filter(transaction_type='expense'):
        expense += float(transaction.amount)
    piece = pie_value(income, tooltip="Income")
    piece.set_on_click('http://localhost:8000/data/transactions/income/')
    plot.append_values(piece)
    piece = pie_value(expense, tooltip="Expense")
    piece.set_on_click('http://localhost:8000/data/transactions/expense/')
    plot.append_values(piece)
    #plot.append_values(pie_value(expense, ("Expense", '#FF33C9')))
    #plot.append_values(pie_value(expense, tooltip="Expense", label="Expense"))
    chart = openFlashChart.template("All Transactions")
    chart.add_element(plot)
    return render_to_response('chart.html', {
        'chart_data': chart.encode(),
    }, context_instance=RequestContext(request))
