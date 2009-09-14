from django.conf.urls.defaults import *

urlpatterns = patterns('redline.categories.views',
    url(r'^$', 'category_list', name='category_list'),
    url(r'^add/$', 'category_add', name='category_add'),
    url(r'^edit/(?P<slug>[\w_-]+)/$', 'category_edit', name='category_edit'),
    url(r'^delete/(?P<slug>[\w_-]+)/$', 'category_delete', name='category_delete'),
    url(r'^lookups/$', 'categoryLookup_list', name='categoryLookup_list'),
    url(r'^lookups/add/', 'categoryLookup_add', name='categoryLookup_add'),
    url(r'^lookups/edit/(?P<lookup_id>\d+)/', 'categoryLookup_edit', name='categoryLookup_edit'),
    url(r'^lookups/delete/(?P<lookup_id>\d+)/', 'categoryLookup_delete', name='categoryLookup_delete'),
)

