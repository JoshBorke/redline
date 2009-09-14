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
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),

    (r'^$', include('redline.budgets.urls')),

    # accounts
    (r'^accounts/', include('redline.accounts.urls')),
    # categories
    (r'^category/', include('redline.categories.urls')),
    # transactions
    (r'^transactions/', include('redline.transactions.urls')),

    # budgets
    (r'^budget/', include('redline.budgets.urls')),
)
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/josh/local/redline/media'}),
        (r'^data-files/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/josh/local/redline/media'}),
    )

