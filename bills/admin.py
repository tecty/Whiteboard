from django.contrib import admin

from .models import Bill,Settle
# Register your models here.
admin.site.register(Bill)
admin.site.register(Settle)
