from django.contrib.auth.models import User
from django.test import TestCase

from django.utils import timezone
from .models import * 
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
        
class SettleTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Create a list of User to be test environment"""
        cls.user001 =User.objects.create_user('u001',"u001@example.cn","tt")
        cls.user002 =User.objects.create_user('u002',"u002@example.cn","tt")
        cls.user003 =User.objects.create_user('u003',"u003@example.cn","tt")
        cls.user004 =User.objects.create_user('u004',"u004@example.cn","tt")

        cls.user_list = [
            cls.user001,
            cls.user002,
            cls.user003,
            cls.user004,
        ]

        # setting up some random bills and users
        # all user pay u0 $20
        cls.bill02 = Bill(title = 'bill02',description = '2', 
            date = timezone.now(),initiate_user = cls.user_list[0]
        )

        split_bill(cls.bill02,{
            cls.user_list[0]:20,
            cls.user_list[1]:20,
            cls.user_list[2]:20,
            cls.user_list[3]:20,
        })
        # all user pay u1 $10
        cls.bill01 = Bill(title = 'bill01',description = '1', 
            date = timezone.now(),initiate_user = cls.user_list[1]
        )

        split_bill(cls.bill01,{
            cls.user_list[0]:5,
            cls.user_list[1]:5,
            cls.user_list[2]:5,
            cls.user_list[3]:5,
        })

        # after these two bill, we should get 50,-5,-25,-25
        cls.settle = Settle(
            start_date = timezone.now(),
            initiate_user = cls.user001,
            msg = "payment Detail",
        )

    def test_get_tr_flag(self):
        # test whether it can get the latest tr flag from sys
        # initial value should be 0
        self.assertEquals(get_latest_tr_flag(),0)


    def test_update_state(self):

        self.assertEquals(self.settle.state, 'PD')
        # update the settle state of this settle to waiting
        # since the bill isn't cleared
        self.settle.update_state()
        self.assertEquals(self.settle.state, 'WT')
        for tr in BillTransation.objects.all():
            # all the bill should be paid 
            tr.set_paid()
            # update the state of the self.settle
            self.settle.update_state()
            
            if is_all_tr_finished():
                # all is done, it would transformm to pcs
                self.assertEquals(self.settle.state, 'PC')
            else:
                # waiting some transation to be paid
                self.assertEquals(self.settle.state, 'WT')
    
    def test_create_settle_transaction(self):
        # test whether the auto generate transaction of settle is correct
        # we should get 50,-5,-25,-25
        for tr in BillTransation.objects.all():
            # all user has paid their bill
            tr.set_paid()
        

    def test_is_all_tr_finished(self):
        self.assertEquals(is_all_tr_finished(),False)
        for tr in BillTransation.objects.all():
            tr.set_paid()
        self.assertEquals(is_all_tr_finished(),True)