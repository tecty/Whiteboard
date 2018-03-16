from django.contrib.auth.models import User
from django.db import models


from .models import Bill,AbstractBaseTransation, BaseTransation,BaseTransation
# decimal calculation support
from decimal import Decimal


# public function to split the bill 
def split_bill(this_bill, portions):

    # save this this_bill first 
    this_bill.save()
    
    for from_user, portion_amount in portions.items():
        # check whether the portion is valid
        if portion_amount >= 1000:
            raise OverflowError('Payer only can safely pay within $1000.')

        # set all transations from payee
        if from_user == this_bill.initiate_user:
            # self pay to self must be paid
            this_bill.billtransation_set.create(
                from_user = from_user, to_user =this_bill.initiate_user,
                amount = portion_amount, state = 'PD'
            )
        else:
            # set the transation that payee shoud pay
            this_bill.billtransation_set.create(
                from_user = from_user, to_user =this_bill.initiate_user,amount = portion_amount
            )
                

    # refresh all the bill's portions and given an initial state
    this_bill.update_finished()
    # don't know what to return 
    return this_bill




def pay_bill(user, bill):
    # this user want to pay this bill

    # serch the transation attach to this bill 
    # need to pay by this user
    bt = bill.billtransation_set.filter(from_user = user)
    
    if  not bt :
        # this user cannot pay this bill
        return False

    # else
    # this user successfully pay this bill
    bt.set_paid()
    return True

def quick_split(this_bill, user_list, total):
    # auto generate the split_bill by user_list 
    # and total amount

    # calculate the split amount
    amount =Decimal(total) /len(user_list)


    # generate the split dictionary
    split_dict = {}
    for uid in user_list:
        this_user = User.objects.get(pk = uid)
        split_dict.update({this_user:amount})
        
    # call the original function to append the bill
    split_bill(this_bill,split_dict)


