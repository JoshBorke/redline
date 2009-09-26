from django.conf.urls.defaults import *
from redline import settings

urlpatterns = patterns('redline.accounts.views',
    url(r'^$', 'accounts_list', name='account_list'),
    url(r'^overview/(?P<year>\d+)/(?P<month>\d+)/$', 'accounts_detail', name='accounts_detail'),
    url(r'^overview/(?P<year>\d+)/(?P<month>\d+)/(?P<ttype>\d+)$', 'accounts_detail_type', name='accounts_detail_type'),
    url(r'^overview/(?P<year>\d+)/(?P<month>\d+)/(?P<ttype>\d+)/(?P<slug>[\w_-]+)/$', 'accounts_category_detail', name='accounts_category_detail'),
    url(r'^add/$', 'account_add', name='account_add'),
    url(r'^edit/(?P<account_id>\d+)/$', 'account_edit', name='account_edit'),
    # for specific accounts
    url(r'^info/(?P<account_id>\d+)/$', 'account_info', name='account_info'),
    url(r'^info/(?P<account_id>\d+)/(?P<year>\d+)/(?P<month>\d+)$', 'account_detail', name='account_detail'),
    url(r'^info/(?P<account_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<ttype>\d+)$', 'account_detail_type', name='account_detail_type'),
    url(r'^info/(?P<account_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<ttype>\d+)/$(?P<slug>[\w_-]+)/', 'account_category_detail', name='account_category_detail'),
    # for misc
    url(r'^delete/(?P<account_id>\d+)/$', 'account_delete', name='account_delete'),
    url(r'^import/(?P<account_id>\d+)/$', 'account_import', name='account_import'),
    # for account types, not used
    url(r'^account_type$', 'account_type_list', name='account_type_list'),
    url(r'^account_type/add/$', 'account_type_add', name='account_type_add'),
    url(r'^account_type/edit/(?P<account_type_id>\d+)/$', 'account_type_edit', name='account_type_edit'),
    url(r'^account_type/delete/(?P<account_type_id>\d+)/$', 'account_type_delete', name='account_type_delete'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/josh/local/redline/media'}),
        (r'^data-files/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/josh/local/redline/media'}),
    )

