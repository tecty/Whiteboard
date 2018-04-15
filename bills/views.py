from django.shortcuts import render,get_list_or_404,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse
from django.utils import timezone

# support for or select
from django.db.models import Q

# view models
from django.views import generic

# apps' model
from .models import Bill,AbstractBaseTransation,BillTransation,cal_balance,check_settle_update,get_latest_tr_flag
# shortcut to split_bill etc
from .shortcut import split_bill,pay_bill,quick_split

# User model from auth
from django.contrib.auth.models import User

# decimal translation support
from decimal import Decimal

# message support
from django.contrib import messages

# @login_required
class IndexView(LoginRequiredMixin,generic.ListView ):
    template_name = 'bills/index.html'
    context_object_name = 'bill_list'
    
    def get_queryset(self):
        """
        self is payee only ignore FN
        self is not payee only want PC
        """
        
        # update the settlement if anyone view this page
        check_settle_update()


        return Bill.objects.filter(
                Q(initiate_user = self.request.user)&
                ~Q(state = 'FN')
                |
                Q(billtransation__from_user= self.request.user) &
                Q(state = 'PC')
            ).distinct()

    def get_context_data(self):
        # Call the base implementation first to get a context
        context = super().get_context_data()
        context['duty_list'] = BillTransation.objects.filter(from_user = self.request.user,state = 'UP')
        # all the activity that associate with this user
        # exclude self payment
        context['history_list'] = BillTransation.objects.\
                filter(Q(from_user = self.request.user)|Q(to_user = self.request.user)).\
                exclude(from_user = self.request.user, to_user = self.request.user).\
                filter(state = 'PD').\
                order_by('id')
        if get_latest_tr_flag():
            # if there is a transaction flag, it add one 
            context['history_list']= context['history_list'].\
                filter(pk__gt = get_latest_tr_flag().id)

        context['balance'] = cal_balance(self.request.user.id)
        return context

# return how the bill is split
class DetailView(generic.DetailView,LoginRequiredMixin):
    template_name ='bills/details.html'
    context_object_name = 'bill'
    model = Bill

@login_required
def create(request):

    # content for create a bill
    content = {
        # who can share this bill
        'stackholder':User.objects.all(),

    }

    return render(request, 'bills/create_form.html',content)

@login_required
def create_respond(request):
    # use the form to create the correspond object


    this_bill = Bill()
    this_bill.description =request.POST['description']
    try:

        this_bill.title =request.POST['title']
        # issue the create date is now
        this_bill.date = timezone.now()
        this_bill.initiate_user =request.user

        # get all the portions distribution
        stackholder = request.POST.getlist('stackholder')
        
        # try to save this bill 
        # create correspond transation
        quick_split(this_bill,stackholder,request.POST['total'])

    except Exception as e:
        # add the failure reason.
        messages.add_message(request, messages.INFO,str(e))

        return render(
            request,'bills/create_form.html',
            {
                'stackholder':User.objects.all(),
            }
        )
    else:
        # got to the detail page of this bill
        return HttpResponseRedirect(reverse('bills:detail', args=(this_bill.id,)))

@login_required
def pay_bill_request(request, bill_id):
    # get the transation associate with this user and bill
    # any modify to un-processing bill in here is invalid
    this_bill = get_object_or_404(Bill,pk =  bill_id,state = 'PC' )
    this_tr = this_bill.billtransation_set.get(from_user =request.user)
    print(this_tr)
    
    # try to pay that 
    if this_tr:
        this_tr.set_paid()


    # return to home 
    return  HttpResponseRedirect(reverse("bills:index"))


@login_required
def decline_bill_request(request,bill_id):
    # get the transation associate with this user and bill
    # any modify to un-processing bill in here is invalid
    this_bill = get_object_or_404(Bill,pk =  bill_id,state = 'PC' )
    this_tr = this_bill.billtransation_set.get(from_user =request.user)
    # try to pay that 
    if this_tr:
        this_tr.set_decline()
    # return to home 
    return  HttpResponseRedirect(reverse("bills:index"))

@login_required
def modify_bill(request, bill_id):
    # 
    # any modify to un-processing bill in here is invalid
    this_bill = get_object_or_404(
        Bill,
        ~Q(state = 'FN'),
        pk =  bill_id,
        initiate_user = request.user
    )
    return render(request,'bills/modify_form.html',{
        'bill':this_bill,
    })

@login_required
def modify_bill_request(request,bill_id):
    # get the bill need to modify,
    # not a payee to modify is invalid
    # a bill if it's finished, it couldn't be modified
    this_bill = get_object_or_404(
        Bill,
        ~Q(state = 'FN'),
        pk =  bill_id,
        initiate_user = request.user
    )


    
    if request.POST['action_type']== 'modify':
        # modify all the transation that attach to this bill
        for tr in this_bill.billtransation_set.all():
            
            if Decimal(request.POST['tr'+str(tr.id)])>= 1000:
                # raise bill amount protection
                raise OverflowError('Payer only can safely pay within $1000.')
            # else, update the tr with unpaid flag
            tr.amount = request.POST['tr'+str(tr.id)]
            tr.save()
            tr.state = 'UP'
        # resume this bill 
        this_bill.set_processing()
    elif request.POST['action_type'] =='resume':
        # make this bill resume, keep the old paid state
        this_bill.set_processing()
    elif request.POST['action_type'] =='suspend':
        # make this bill suspend
        this_bill.set_pending()
    elif request.POST['action_type'] =='delete':
        # delete the bill
        this_bill.delete()
        # couldn't get to the detail page, go to the index
        return HttpResponseRedirect(reverse('bills:index'))
        
    # redirect to this bill's detials page
    return HttpResponseRedirect(reverse('bills:detail',args = (this_bill.id,)))