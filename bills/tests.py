from django.contrib.auth.models import User
from django.test import TestCase

from django.utils import timezone
from .shortcut import *



# Create your tests here.

class BillModelTests(TestCase):
    def setUp(self):
        """Create a list of User to be test environment"""
        self.user001 =User.objects.create_user('u001',"u001@example.cn","tt")
        self.user002 =User.objects.create_user('u002',"u002@example.cn","tt")
        self.user003 =User.objects.create_user('u003',"u003@example.cn","tt")
        self.user004 =User.objects.create_user('u004',"u004@example.cn","tt")

        self.user_list = [
            self.user001,
            self.user002,
            self.user003,
            self.user004,
        ]

    def test_create_split_bill(self):
        """
        Split bill should create all the small transations go 
        alone with the given bill
        """
        # u001 create a lunch bill
        lunch_bill = Bill(
            title = "Lunch", description = "Today's Lunch", 
            date = timezone.now(),initiate_user = self.user001
        )

        # try to save lunch bill 
        lunch_bill.save()

        # contruct the split
        split_amount= 20/4
        split = {
            self.user_list[0]:split_amount,
            self.user_list[1]:split_amount,
            self.user_list[2]:split_amount,
            self.user_list[3]:split_amount,
        }


        # everyone should pay to u001 for total $20
        split_bill(this_bill = lunch_bill, portions = split)


        # all the bill's transation
        transation_list = lunch_bill.billtransation_set.all()


        for tr in transation_list:
            # test all the seperate bill has correct amount 
            self.assertEqual(tr.amount, split_amount)

            # all the user should pay to user001 
            self.assertEqual(tr.to_user, self.user_list[0])

            # all the payee is in the user group
            self.assertTrue(tr.from_user in  self.user_list)

    def test_cal_balance(self):

        # the start status shoud be 0
        self.assertEqual(
            cal_balance(self.user_list[0].id),0        
        )
        self.assertEqual(
            cal_balance(self.user_list[1].id),0        
        )
        self.assertEqual(
            cal_balance(self.user_list[2].id),0        
        )
        self.assertEqual(
            cal_balance(self.user_list[3].id),0        
        )


        # make a bunch of transation

        # u1 trans to u0  $10
        bill01 = Bill(title = 'bill01',description = '1', 
            date = timezone.now(),initiate_user = self.user_list[0]
        )

        split_bill(bill01, {self.user_list[1]:10})

        for bt in bill01.billtransation_set.all():
            # everyone has pay the bill
            bt.set_paid()
        

        self.assertEqual(
            cal_balance(self.user_list[0].id),10        
        )
        self.assertEqual(
            cal_balance(self.user_list[1].id),-10
        )
    def test_cal_balance2(self):

        # the start status shoud be 0
        self.assertEqual(
            cal_balance(self.user_list[0].id),0        
        )
        self.assertEqual(
            cal_balance(self.user_list[1].id),0        
        )
        self.assertEqual(
            cal_balance(self.user_list[2].id),0        
        )
        self.assertEqual(
            cal_balance(self.user_list[3].id),0        
        )

        # all user pay u0 $20
        bill02 = Bill(title = 'bill02',description = '2', 
            date = timezone.now(),initiate_user = self.user_list[0]
        )

        split_bill(bill02,{
            self.user_list[0]:20,
            self.user_list[1]:20,
            self.user_list[2]:20,
            self.user_list[3]:20,
        })

        for bt in bill02.billtransation_set.all():
            # everyone has pay the bill
            bt.set_paid()
        
        self.assertEqual(
            cal_balance(self.user_list[0].id),60        
        )
        self.assertEqual(
            cal_balance(self.user_list[1].id),-20       
        )
        self.assertEqual(
            cal_balance(self.user_list[2].id),-20      
        )
        self.assertEqual(
            cal_balance(self.user_list[3].id),-20       
        )


    def test_quick_split(self):
        # u001 create a lunch bill
        lunch_bill = Bill(
            title = "Lunch", description = "Today's Lunch", 
            date = timezone.now(),initiate_user = self.user001
        )
        # use quick split to split the bill
        quick_split(lunch_bill,
            [
                self.user001.id, 
                self.user002.id,
                self.user003.id,
                self.user004.id,
            ],
            20
        )


        # the start status shoud be when no one pay the bill
        self.assertEqual(
            cal_balance(self.user_list[0].id),0        
        )
        self.assertEqual(
            cal_balance(self.user_list[1].id),0        
        )
        self.assertEqual(
            cal_balance(self.user_list[2].id),0        
        )
        self.assertEqual(
            cal_balance(self.user_list[3].id),0        
        )


        for bt in lunch_bill.billtransation_set.all():
            # everyone has pay the bill
            bt.set_paid()
        
        # expect u001, everyone should have -5
        self.assertEqual(
            cal_balance(self.user_list[0].id),15        
        )
        self.assertEqual(
            cal_balance(self.user_list[1].id),-5       
        )
        self.assertEqual(
            cal_balance(self.user_list[2].id),-5      
        )
        self.assertEqual(
            cal_balance(self.user_list[3].id),-5       
        )