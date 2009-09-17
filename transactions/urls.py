from django.conf.urls.defaults import *

urlpatterns = patterns('redline.transactions.views',
    url(r'^list$', 'transaction_list', name='redline_transaction_list'),
    url(r'^add/$', 'transaction_add', name='redline_transaction_add'),
    url(r'^edit/(?P<transaction_id>\d+)/$', 'transaction_edit', name='redline_transaction_edit'),
    url(r'^edit/ajax/amount', 'transaction_ajax_edit_amount', name='transaction_ajax_amount'),
    url(r'^edit/ajax/type', 'transaction_ajax_edit_type', name='transaction_ajax_type'),
    url(r'^delete/(?P<transaction_id>\d+)/$', 'transaction_delete', name='redline_transaction_delete'),
    url(r'^$', 'data_overview'),
    url(r'^(?P<t_type>income|expense)/$', 'data_expense_or_income'),
    url(r'^test/$', 'chart_test'),
    #url(r'^(?P<t_type>income|expense)/$', 'data_expense_or_income'),
    #url(r'^(?P<cat>.*)/$', 'data_category'),
)
