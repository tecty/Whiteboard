from django.shortcuts import render,get_list_or_404,get_object_or_404
from bills.models import Settle, SettleTransaction,get_settle_tr,get_unpaid_tr
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect,HttpResponse,Http404
from django.db.models import Sum
from django.urls import reverse
import datetime
# view models
from django.views import generic
# message support
from django.contrib import messages


# Create your views here.
class IndexView(LoginRequiredMixin,generic.ListView ):
    template_name = 'settle/index.html'
    context_object_name = 'settle_list'
    model = Settle
    def get_context_data(self):
        # Call the base implementation first to get a context
        context = super().get_context_data()
        context['my_settle'] = get_settle_tr(self.request.user)

        return context
    

@login_required
def details(request, pk):
    context = {}
    context["settle"] =Settle.objects.get(pk = pk)  
    context['unpaid_list'] = context['settle'].get_unpaid_tr()
    # get the responsible_tr for this user
    context['responsible_tr'] = context['settle'].\
        get_responsible_tr(request.user)

    if request.user.is_superuser:
        # only the super upser can have a total view of the settlement
        context["settle_tr"] =Settle.objects.get(pk = pk).settletransaction_set.all()
        return render(request, 'settle/detail_admin.html',context)
    else :
        # the login user is not a super, return the normal page to pay
        # fetch the transaction information
        context['my_settle_tr'] = Settle.objects.get(pk = pk).\
            settletransaction_set.get(reset_tr__to_user = request.user)
        return render(request, "settle/detail_user.html",context)

@login_required
def tr_details(request,pk):
    context = {}
    context["settle_tr"] =SettleTransaction.objects.get(pk = pk)  
    return render(request, 'settle/tr_details.html',context)


@login_required
def create(request):
    if request.user.is_superuser:
        return render(request,'settle/create_form.html')
    else:
        return Http404(request, "Must be Admin to create Settle.")

@login_required
def create_respond(request):
    if not request.user.is_superuser:
        raise Http404(request,"Must be Admin to create Settle.")
    try:
        # try to save a new settle into database
        settle = Settle(
                start_date = datetime.datetime.\
                        strptime(request.POST['date'],
                            "%d %B, %Y").\
                        strftime("%Y-%m-%d %H:%M"),
                initiate_user = request.user,
                msg = request.POST['msg'],
            )
        settle.save()
    except Exception as e:
        # push sth to messager
        messages.add_message(request, messages.INFO,str(e))

        return render(
            request,'settle/create_form.html'
        )
    return HttpResponseRedirect(reverse('settle:detail', args=(settle.id,)))


@login_required
def pay_settle(request, pk):
    try:
        my_tr =Settle.objects.get(pk = pk).settletransaction_set.\
                    get(reset_tr__to_user = request.user)
        my_tr.set_paid()
    except Exception as e:
        # catch all the exception 
        raise Http404(request, 
            "Couldn't find correspond transaction or settlemment.")

    # redirect to the detail's page
    return HttpResponseRedirect(reverse('settle:detail',args=(pk,)))

@login_required
def verify_tr_request(request,pk):
    st = get_object_or_404(SettleTransaction,pk = pk )
    st.set_verified(request.user)
    return HttpResponseRedirect(reverse('settle:detail',args=(st.settle.id,)))

@login_required
def decline_tr_request(request,pk):
    st = get_object_or_404(SettleTransaction,pk = pk )
    st.set_unpaid()
    return HttpResponseRedirect(reverse('settle:detail',args=(st.settle.id,)))

@login_required
def print_outgo(request,pk):
    # the settle_tr that need to print
    settle = get_object_or_404(Settle,pk = pk )
    # the context for this printable page
    context = {}
    # get the responsible_tr for this user
    context['responsible_tr'] = settle.\
        get_responsible_tr(request.user ,"outgo")
    # outgo doesn't have specific method for that
    context['subtotal'] = -context['responsible_tr'].\
        aggregate(Sum('amount'))['amount__sum']
        
    if request.user != settle.initiate_user:
        # initiate user don't have  this
        context['my_settle_tr'] = settle.settletransaction_set.\
            get(reset_tr__to_user = request.user)
        # calculate the total fe
        context['total'] =context['subtotal'] \
            - context['my_settle_tr'] .cal_penalty() \
            - context['my_settle_tr'].service_fee

    return render(request,
        "settle/part/outgo_statement.html",context=context)
@login_required
def print_tr(request,pk):
    # the settle_tr that need to print
    settle = get_object_or_404(Settle,pk = pk )
    # the context for this printable page
    context = {}
    # get the responsible_tr for this user
    context['responsible_tr'] = settle.\
        get_responsible_tr(request.user ,"outgo")
    if request.user != settle.initiate_user:
        context['my_settle_tr'] = settle.settletransaction_set.\
            get(reset_tr__to_user = request.user)
    return render(request,
        "settle/part/transaction_statement.html",context=context)