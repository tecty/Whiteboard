from django.db import models
# support for user reference 
from django.contrib.auth.models import User
# use a transation and the bills
from bills.models import AbstractBaseTransation,Bill 
# support tieme calculation
from django.utils import timezone

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
            blank = True
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
            # should wait for some unfinished transation
            self.state = 'WT'


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