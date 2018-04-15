from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
# decimal calculation support
from decimal import Decimal,getcontext
def cal_balance(User_id):
    if type(User_id) == User:
        this_user = User_id
    elif type(User_id) == int:
        # calculate the  user's balance 
        this_user = User.objects.get(pk = User_id)
    else:
        raise TypeError("Only support user and int for cal_balance")
    # latest tr flag that settled 
    """
        HERE IS SHIT
        settled_tr_flag = get_latest_tr_flag().id
    """ 
    settled_tr_flag = 0
    

    # all the money he could get
    receive = AbstractBaseTransation.objects.\
                filter(
                    to_user = this_user,
                    state = 'PD',
                    # only get the transaction after settlement
                    id__gt = settled_tr_flag 

                ).aggregate(models.Sum('amount'))['amount__sum'] 
                
    # all the money he should spend
    spend = AbstractBaseTransation.objects.\
                filter(
                    from_user = this_user,
                    state = 'PD',
                    # only get the transaction after settlement
                    id__gt = settled_tr_flag 
                ).aggregate(models.Sum('amount'))['amount__sum']


    # make them as Decimal
    if not receive:
        receive = Decimal(0)
    if not spend:
        spend = Decimal(0)

    # return the balance it current has
    return receive - spend

def get_latest_tr_flag():
    # return the latest tr_flag to reduce the amount of
    # database request
    # require the latest Finished Settle bill
    latest_settle = Settle.objects.filter(state = 'FN').\
                        order_by('-id').first()
    if latest_settle:
        # this system has a settle return the latest tr_flag
        return latest_settle.tr_flag
    else:
        # this system doesn't have a settle
        return 0

def get_unpaid_tr(id_range = None):
    if id_range:
        # all the bills that in the range also is not paid
        return BillTransation.objects.filter(
            id__gte = id_range[0],
            id__lte = id_range[1]
        ).exclude(state = 'PD')

    # else use the old way to provide unpaid tr.
    # return all the unfinished transation between the id range
    return BillTransation.objects.exclude(
        # all the transation that include in this settle
            state ='PD'
        ).filter(
            # only get the transaction after the previous settlement
            id__gt = get_latest_tr_flag()
        )


def count_tr(this_user):
    # count the acutall transactions (exclude self payment)
    return AbstractBaseTransation.objects.filter(
            id__gt = get_latest_tr_flag())\
        .filter(
            Q(from_user = this_user) | Q(to_user = this_user)
        ).exclude(Q(from_user = this_user) & Q(to_user = this_user) )\
        .distinct()\
        .aggregate(models.Count('id'))['id__count']
        # because count is id, so the field name is id__count

def check_settle_update():
    # check all the not finished settlements' update
    settle_set = Settle.objects.exclude(state = 'FN')
    for s in settle_set:
        # update all the settle need to update
        s.update_state()

def get_settle_tr(this_user):
    ret = None
    try:
        # get the settle transaction of this user
        ret = SettleTransaction.objects.\
                order_by("-id").\
                exclude(state = 'FN').\
                filter(reset_tr__to_user = this_user).\
                get()
    except Exception as identifier:
        # unkown error when no settlement in the system
        pass
    return ret

# Create your models here.
class Bill(models.Model):
    """ The information of that particular bill."""
    title = models.CharField(max_length = 255)
    # description can be not provided
    description = models.CharField(max_length = 1023,blank = True)
    date = models.DateTimeField('Initiated Date')
    initiate_user = models.ForeignKey(User,on_delete = models.PROTECT)
    # set states, the initial state is Processing
    state = models.CharField(max_length = 2, 
        choices = (
            ('PD','Pending'),
            ('PC','Processing'),
            ('FN','Finished'),
        ),
        default = 'PC',
    )

    def __str__(self):
        return self.title

    def set_pending(self):
        # set this bill to pending
        self.state = 'PD'

        for bt in self.billtransation_set.all():
            # set all the bill transation to suspend
            bt.set_suspend()
        
        # save the status of this bill
        self.save()

    def set_processing(self):
        # set this bill to processing
        self.state = 'PC'

        for bt in self.billtransation_set.all():
            # set all the bill transation to processing
            bt.set_processing()

        # save this bill
        self.save()
        
    def check_finished(self):
        # whether the state is finished
        for bt in self.billtransation_set.all():
            # set all the bill transation to processing
            if bt.state != 'PD':
                # if one of the bill is not successfully paid, set processing
                return False
        # All transations has been paid
        return True
    def update_finished(self):
        # a bill only can switch to finished when it is processing
        if self.state=='PC' and self.check_finished():
            self.state = 'FN'
            self.save()
    

    # helper function to show the state of the bill
    def is_finished(self):
        return self.state == 'FN'
    def is_processing(self):
        return self.state == 'PC'
    def is_pending(self):
        return self.state == 'PD'




class AbstractBaseTransation(models.Model):
    """Every unit of Transation """

    # coulnd't delete a user that currently has transation
    from_user = models.ForeignKey(User,on_delete = models.PROTECT,related_name = "from_user")
    to_user = models.ForeignKey(User,on_delete = models.PROTECT,related_name = "to_user")

    # to record the amount of this transation
    amount = models.DecimalField(max_digits = 7, decimal_places = 2)
    def __str__(self):
        return str(self.from_user) + " paid "+ str(self.to_user)+ " $" +str(self.amount)


        # set different states, defults is Unpaid
    state = models.CharField(max_length = 2, 
        choices = (
            ('UP','Unpaid'),
            ('SU','Suspend-Unpaid'),
            ('PD','Paid'),
            ('SP','Suspend-Paid'),
            ('DC','Decliend'),
        ),
        default= 'UP',
    )
    def set_suspend(self):
        if self.state == 'PD':
            self.state = 'SP'
        if self.state == 'UP':
            self.state = 'SU'
        # save the status
        self.save()

    def set_processing(self):
        # reverse the set_suspend and remove Decliend 
        if self.state == 'SP':
            self.state = 'PD'
        if self.state  in ['SU','DC']:
            # solve decliend and unpaid can pay
            self.state = 'UP'
        # save the status
        self.save()
    def set_decline(self):
        # set this transation to decliend
        self.state = "DC"
        # save the status 
        self.save()
        # set bill to pending
        self.bill.set_pending()

    def set_paid(self):
        # set the state of this bill and 
        # refresh the bills' state and save
        self.state = "PD"
        self.save()

        self.bill.update_finished()


class BaseTransation(AbstractBaseTransation):
    """A Transation that has nothing """



class BillTransation(AbstractBaseTransation):
    """this would have the transtaion to link to a bill"""

    bill = models.ForeignKey(Bill, on_delete = models.CASCADE)

"""
    Settle Part


"""


class Settle(models.Model):
    """ Settle is a model to make all balance back to 0."""
    # start to make the settle
    start_date = models.DateTimeField();
    # even the transation is gone, it would still need to preserve this flag
    # to make the settle work for all the time
    tr_flag = models.ForeignKey(
            AbstractBaseTransation,
            on_delete = models.PROTECT,
            null = True
        )
    # who should be responsible for this payment
    initiate_user = models.ForeignKey(User, on_delete= models.PROTECT)
    # detail for payment method
    msg = models.CharField(max_length =1024)
    # some state attach with settle
    # admin always settled before the end of cycle.
    state = models.CharField(max_length = 2,
        choices = (
            ('PD','Pending'),
            ('WT','Waitting'),
            ('PC','Processing'),
            ('VR','Verifying'),
            ('FN','Finished'),
        ),
        default = 'PD',
    )

    def __str__(self):
        return str(self.start_date.date())+" Settlement"


    def check_paid(self,tr_set):
        ret = 'FN'
        for tr in tr_set:
            if tr.state == 'UP':
                return 'PC'
            elif ret == 'VD' and tr.state == 'PD' :
                # varifying this bill 
                ret = 'VR'
                continue
            elif ret == 'VD' and tr.state == 'VD':
                continue
        # return the lowest status to set the status.
        return ret

    def update_state(self):
        if self.state =='FN':
            # do nothing to keep this settle's state
            return 
            
        if timezone.now()<= self.start_date:
            # this settle is not started ye
            self.state = 'PD'
            self.save()
            return self
        # all the transation that include in this settle
        tr_set = self.settletransaction_set.all()
        if tr_set:
            # update state by a spearate function
            self.state = self.check_paid(tr_set)
            if self.state =='FN':
                # if here's state == 'Finished'
                # then here is the first time this settle has finished 
                # settup the trflag
                # print(self.get_responsible_tr_range()[1])
                self.tr_flag = AbstractBaseTransation.\
                    objects.get(id = self.get_responsible_tr_range()[1])
            
        else:
            if self.is_all_tr_finished():
                # start processing this bill
                # get all the user in the system except the initiate user
                user_list = User.objects.exclude(
                        id = self.initiate_user.id ,
                    ) 
                # setting all the transation should be made
                for u in user_list:
                    # setting up all the transactions 
                    self.create_settle_transaction(u)
                
                self.state = 'PC'
            else:
                # should wait for some unfinished transation
                self.state = 'WT'
        # save the new state to database
        self.save()

    def get_unpaid_tr(self):
        # remapping the public function that takes the settles attribute
        return get_unpaid_tr(self.get_responsible_tr_range())
    def is_all_tr_finished(self):
        # return true if all the transaction before now 
        # is finished, else return false
        if self.get_unpaid_tr():
            return False
        return True
    def get_responsible_tr(self,this_user,type = 'transaction'):
        res_range = self.get_responsible_tr_range()
        # return the transaction that in the range
        if type =='transaction':
            return BillTransation.objects.filter(
                id__gte = res_range[0],id__lte = res_range[1]).filter(
                Q(from_user = this_user) | Q(to_user = this_user)
                ).exclude(Q(from_user = this_user) & Q(to_user = this_user) )\
                .distinct()
        elif type== 'outgo':
            # only care about howmuch it has paid
            return BillTransation.objects.filter(
                id__gte = res_range[0],
                id__lte = res_range[1],
                from_user = this_user
            )

    def get_responsible_tr_range (self):
        # return the transactionset that this settlement need to care
        # about
        settle_set = Settle.objects.order_by("-id")
        
        res_tr = [0,0]
        if settle_set.count()>=2:
            # the previous trflag must not null
            res_tr[0] = settle_set[1].tr_flag+1
            # refresh the default value of res_tr
            res_tr[1] = res_tr[0]

            # the next one would be decided by the last bill by the due date
            last_res_bill = Bill.objects.filter(date__lt = settle_set[1].start_date).\
                order_by("-id").first()
            if last_res_bill:
                res_tr[1] = last_res_bill.billtransation_set.order_by("-id").\
                    first().id
        else:
            # only has one settle in the set 
            # the next one would be decided by the last bill by the due date
            last_res_bill = Bill.objects.filter(date__lt = settle_set[0].start_date).\
                order_by("-id").first()
            if last_res_bill:
                res_tr[1] = last_res_bill.billtransation_set.order_by("-id").\
                    first().id
        return res_tr

    def create_settle_transaction(self,user):
        # a helper function
        # create the settle transation form the user to initiate_user

        # the actual that reset the balance 
        actual_transaction= BaseTransation(
            from_user = self.initiate_user,
            to_user = user,
            amount = -cal_balance(user),
            state='PD'
        )
 
        # save the acutal transation for both cases
        actual_transaction.save()
        
        # create settle transation to link them together
        # 
        # Service fee is
        # for every transaction, should pay 0.02 for each transaction
        self.settletransaction_set.create(
            reset_tr = actual_transaction,
            service_fee = count_tr(user)*0.02,
        )

        # save the status in to data base
        self.save()


# Create your models here.
class SettleTransaction(models.Model):
    """Special transation that set all balance to 0"""
    # overwrite the state
    
    state = models.CharField(max_length = 2, 
        choices = (
            ('UP','Unpaid'),
            ('PD','Verifying'),
            ('VD','Paid'),
        ),
        default= 'UP',
    )

    def __str__(self):
        return str(self.reset_tr.from_user) +\
                " pay to "+ str(self.reset_tr.to_user) + \
                " with fee " +\
                str(self.service_fee)
    # foreign key to this settlement
    settle = models.ForeignKey(Settle,on_delete = models.CASCADE)
    # foreign key to the reset transation
    reset_tr = models.ForeignKey(AbstractBaseTransation,on_delete= models.CASCADE)

    # fee to using this system
    service_fee = models.DecimalField(max_digits = 7, decimal_places = 2)
    # penalty for late paymment 
    penalty = models.DecimalField(max_digits = 7, decimal_places = 2,default = 0)
    
    def cal_penalty(self):
        # calculate the due date
        due_date = self.settle.start_date+ datetime.timedelta(days = 7)

        # calculate the days that has delay 
        delay_days = (timezone.now() - due_date).days

        # must have paid the bill within 7 days, otherwise, calculate the penalty
        if self.state != 'UP' or delay_days <0 :
            # before the due time
            # self.penalty has default value 0
            return self.penalty
        else:
            # calculate the penalty
            # penalty would start from 50 + should pay * (1+0.003)^(delay_days) 
            penalty = 50 



            # generate the penalty by delay days
            penalty = (penalty+ self.service_fee+ self.reset_tr.amount) *\
                        Decimal(format(
                            pow ((1.003), (delay_days+1))
                        , ".15g"))
            return penalty - self.get_reset_amount() - self.service_fee

    def get_reset_amount(self):
        # remap the amount from reset transaction
        return self.reset_tr.amount

    def cal_total(self):
        if self.state ==  'UP':
            # the payer doesn't pay the settle yet
            # summing up all the money user should pay
            return (self.get_reset_amount()+ self.service_fee + self.cal_penalty()).quantize(Decimal('0.00'))

        else:
            # calculate the sum in current record
            return self.get_reset_amount()+ self.service_fee + self.penalty

    def set_paid(self):
        # record the panalty calculation in to system
        self.penalty = self.cal_penalty()
        # set the transaction to be verify
        self.state = "PD"
        # save to database and refresh the settle's state
        self.save()
        self.settle.update_state()
        return self
    def set_unpaid(self):
        # record the panalty calculation in to system
        self.penalty = self.cal_penalty()
        # set the transaction to be verify
        self.state = "UP"
        # save to database and refresh the settle's state
        self.save()
        self.settle.update_state()
        return self
    def set_verified(self, varify_user):
        if varify_user == self.settle.initiate_user:
            # refresh the state of this transaction
            # save it to database
            self.state = "VD"
            self.save()

            # refresh of this settle
            self.settle.update_state()
            return True

        else:
            # permission deny
            return False