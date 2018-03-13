from django.db import models
# use a transation and the bills
from ..models import AbstractBaseTransation,Bill 
# support tieme calculation
from django.utils import timezone
class Settle(models.model):
    """ Settle is a model to make all balance back to 0."""
    # start to make the settle
    start_date = models.DateField();
    # even the transation is gone, it would still need to preserve this flag
    # to make the settle work for all the time
    tr_flag = models.ForeignKey(AbstractBaseTransation, on_delete = models.PROTECT)
    # no needs to initiate user, only admin can change it 
    # some state attach with settle
    # admin always settled before the end of cycle.
    state = models.CharField(max_length = 2,
        choice= (
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
        ret = 'VD'
        for tr in tr_set:
            if tr.state == 'UP':

                return 'PC'
        

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
            # wait for all tr is clear, set tr flag
            # start processing this bill
            self.state = 'PC'
            # TODO: set trs

# Create your models here.
class SettleTransation(AbstractBaseTransation):
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
    # foreign key 
    settle = models.ForeignKey(Settle,on_delete = models.CASCADE)