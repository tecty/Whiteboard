from django.db import models
from django.contrib.auth.models import User



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
    pass



class BillTransation(AbstractBaseTransation):
    """this would have the transtaion to link to a bill"""
    bill = models.ForeignKey(Bill, on_delete = models.CASCADE)

