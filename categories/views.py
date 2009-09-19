from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from redline.categories.models import Category, CategoryLookup
from redline.categories.forms import CategoryForm, CategoryLookupForm

def category_list(request, model_class=Category, template_name='categories/list.html'):
    """
    A list of category objects.

    Templates:  ``categories/list.html``
    Context:
        categories
            paginated list of category objects
        paginator
            A Django Paginator instance
        page
            current page of category objects
    """
    category_list = model_class.active.order_by('name')
    try:
        paginator = Paginator(category_list, getattr(settings, 'LIST_PER_PAGE', 50))
        page = paginator.page(request.GET.get('page', 1))
        categories = page.object_list
    except InvalidPage:
        raise Http404('Invalid page request.')
    return render_to_response(template_name, {
        'categories': categories,
        'paginator': paginator,
        'page': page,
    }, context_instance=RequestContext(request))

def category_add(request, form_class=CategoryForm, template_name='categories/add.html'):
    """
    Create a new tag object.

    Templates: ``categories/add.html``
    Context:
        form
            a tag form
    """
    if request.POST:
        form = form_class(request.POST)

        if form.is_valid():
            tag = form.save()
            return HttpResponseRedirect(reverse('category_list'))
    else:
        form = form_class()
    return render_to_response(template_name, {
        'form': form,
    }, context_instance=RequestContext(request))

def category_edit(request, slug, model_class=Category, form_class=CategoryForm, template_name='categories/edit.html'):
    """
    Edit a tag object.

    Templates: ``categories/edit.html``
    Context:
        tag
            the existing tag object
        form
            a tag form
    """
    category = get_object_or_404(model_class.active.all(), slug=slug)
    if request.POST:
        form = form_class(request.POST, instance=category)

        if form.is_valid():
            category = form.save()
            return HttpResponseRedirect(reverse('category_list'))
    else:
        form = form_class(instance=category)
    return render_to_response(template_name, {
        'category': category,
        'form': form,
    }, context_instance=RequestContext(request))

def category_delete(request, slug, model_class, template_name='categories/delete.html'):
    """
    Delete a tag object.

    Templates: ``categories/delete.html``
    Context:
        tag
            the existing tag object
    """
    category = get_object_or_404(model_class.active.all(), slug=slug)
    if request.POST:
        if request.POST.get('confirmed') and request.POST['confirmed'] == 'Yes':
            category.delete()
        return HttpResponseRedirect(reverse('category_list'))
    return render_to_response(template_name, {
        'category': category,
    }, context_instance=RequestContext(request))

def categoryLookup_list(request):
    """
    A list of category lookup objects.

    Templates:  ``categories/lookup-list.html``
    Context:
        tags
            paginated list of tag objects
        paginator
            A Django Paginator instance
        page
            current page of category objects
    """
    lookups_list = CategoryLookup.objects.order_by('category')
    try:
        paginator = Paginator(lookups_list, getattr(settings, 'LIST_PER_PAGE', 50))
        page = paginator.page(request.GET.get('page', 1))
        lookups = page.object_list
    except InvalidPage:
        raise Http404('Invalid page request.')
    return render_to_response('categories/lookup-list.html', {
        'lookups': lookups,
        'paginator': paginator,
        'page': page,
    }, context_instance=RequestContext(request))

def categoryLookup_add(request):
    if request.POST:
        form = CategoryLookupForm(request.POST)

        if form.is_valid():
            lookup = form.save()
            # apply the regex to all transactions
            lookup.applyToTransactions()
            return HttpResponseRedirect(reverse('categoryLookup_list'))
    else:
        form = CategoryLookupForm()
    return render_to_response('categories/lookup-add.html', {
        'form': form,
    }, context_instance=RequestContext(request))

def categoryLookup_edit(request, lookup_id, model_class=CategoryLookup, form_class=CategoryLookupForm, template_name='categories/lookup-edit.html'):
    lookup = get_object_or_404(model_class.objects.all(), id = lookup_id)
    if request.POST:
        form = form_class(request.POST, instance=lookup)

        if form.is_valid():
            lookup = form.save()
            lookup.applyToTransactions()
            return HttpResponseRedirect(reverse('categoryLookup_list'))
    else:
        form = form_class(instance=lookup)
    return render_to_response(template_name, {
        'lookup': lookup,
        'form': form,
    }, context_instance=RequestContext(request))
    #return HttpResponseRedirect(reverse('categoryLookup_list'))

def categoryLookup_delete(request, lookup_id):
    return HttpResponseRedirect(reverse('categoryLookup_list'))
