from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from bills.models import Bill
from bills.shortcut import split_bill
from .models import Settle,get_latest_tr_flag
# Create your tests here.
class SettleTest(TestCase):
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

        # setting up some random bills and users
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
        # all user pay u1 $10
        bill01 = Bill(title = 'bill01',description = '1', 
            date = timezone.now(),initiate_user = self.user_list[1]
        )

        split_bill(bill01,{
            self.user_list[0]:5,
            self.user_list[1]:5,
            self.user_list[2]:5,
            self.user_list[3]:5,
        })

        # after these two bill, we should get 50,-5,-25,-25

    def test_get_tr_flag(self):
        # test whether it can get the latest tr flag from sys
        # initial value should be 0
        self.assertEquals(get_latest_tr_flag(),0)


    def test_create_settle(self):
        settle = Settle(
                start_date = timezone.now(),
                initiate_user = self.user001,
                msg = "payment Detail",
            )
        self.assertEquals(settle.state, 'PD')
        # update the settle state of this settle to waiting
        # since the bill isn't cleared
        settle.update_state()
        self.assertEquals(settle.state, 'WT')