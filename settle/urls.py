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
    # path('pay/<int:bill_id>',views.pay_bill_request,name = 'pay'),
    # path('decline/<int:bill_id>',views.decline_bill_request,name = 'decline'),
    # path('modify/<int:bill_id>',views.modify_bill,name = 'modify'),
    # path('modify_request/<int:bill_id>',views.modify_bill_request,name = 'modify_respond'),
]
