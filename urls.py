from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^redline/', include('redline.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    (r'^finances/admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^finances/admin/(.*)', admin.site.root),

    (r'^finances/$', include('redline.budgets.urls')),

    # accounts
    (r'^finances/accounts/', include('redline.accounts.urls')),
    # categories
    (r'^finances/category/', include('redline.categories.urls')),
    # transactions
    (r'^finances/transactions/', include('redline.transactions.urls')),

    # budgets
    (r'^finances/budget/', include('redline.budgets.urls')),
)
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/josh/local/redline/media'}),
        (r'^data-files/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/josh/local/redline/media'}),
    )

