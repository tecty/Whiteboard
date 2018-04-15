from django.urls import path
from . import views

# this_app name is bills
app_name = 'settle'


urlpatterns = [
    path('',views.IndexView.as_view(), name= 'index'),
    path('create',views.create,name='create'),
    path('create_respond',views.create_respond,name='create_respond'),
    path('detail/<int:pk>',views.details,name = 'detail'),
    path('pay/<int:pk>',views.pay_settle,name = 'pay'),
    path('verified/<int:pk>',views.verify_tr_request,name = 'verified'),
    path('decline/<int:pk>',views.decline_tr_request,name = 'decline'),
    path('print_outgo/<int:pk>',views.print_outgo,name = 'print_outgo'),
    path('print_tr/<int:pk>',views.print_tr,name = 'print_tr'),
]
