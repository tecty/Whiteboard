from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# decimal calculation support
from decimal import Decimal
def cal_balance(User_id):
    # calculate the  user's balance 
    this_user = User.objects.get(pk = User_id)

    # latest tr flag that settled 
    settled_tr_flag = get_latest_tr_flag()

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

def get_unpaid_tr():
    # return all the unfinished transation
    return AbstractBaseTransation.objects.exclude(
            state ='PD'
        ).filter(
            # only get the transaction after settlement
            id__gt = get_latest_tr_flag()
        )

def is_all_tr_finished():
    # return true if all the transaction before now 
    # is finished, else return false
    if get_unpaid_tr():
        return False
    return True


class Settle(models.Model):
    """ Settle is a model to make all balance back to 0."""
    # start to make the settle
    start_date = models.DateField();
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
        return "Settle on "+ str(self.start_date )


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
        if self.start_date > timezone.now():
            # this settle is not started ye
            self.state = 'PD'
            self.save()
            return self
        # all the transation that include in this settle
        tr_set = self.settletransation_set.all()
        if tr_set:
            # update state by a spearate function
            self.state = self.check_paid(tr_set)
        else:
            if is_all_tr_finished():
                # start processing this bill
                # TODO: set trs
                self.state = 'PC'
            else:
                # should wait for some unfinished transation
                self.state = 'WT'
        # save the new state to database
        self.save()

def create_settle_transaction(user, init_user):
    # create the settle transation form the user to init_user
    pass
    # if :
    #     pass
    # this_transaction = BaseTransation()

# Create your models here.
class SettleTransation(models.Model):
    """Special transation that set all balance to 0"""
    # overwrite the state
    
    state = models.CharField(max_length = 2, 
        choices = (
            ('UP','Unpaid'),
            ('PD','Paid-Verifying'),
            ('VD','Verified'),
        ),
        default= 'UP',
    )
    # foreign key to this settlement
    settle = models.ForeignKey(Settle,on_delete = models.CASCADE)
    # foreign key to the reset transation
    reset_tr = models.ForeignKey(AbstractBaseTransation,on_delete= models.CASCADE)

    # fee to using this system
    service_fee = models.DecimalField(max_digits = 7, decimal_places = 2)
    # penalty for late paymment 
    penalty = models.DecimalField(max_digits = 7, decimal_places = 2)
    
    def cal_penalty(self):
        pass
    def set_service_fee(self):
        self.service_fee = 0.02 