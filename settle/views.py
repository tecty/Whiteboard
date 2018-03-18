from django.shortcuts import render,get_list_or_404,get_object_or_404
from bills.models import Settle, SettleTransaction,get_settle_tr,get_unpaid_tr
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect,HttpResponse,Http404
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
    context['unpaid_list'] = get_unpaid_tr()
    return render(request, 'settle/details.html',context)

@login_required
def tr_details(request,pk):
    context = {}
    context["settle_tr"] =SettleTransaction.objects.get(pk = pk)  
    return render(request, 'settle/tr_details.html',context)


@login_required
def create(request):
    return render(request,'settle/create_form.html')

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