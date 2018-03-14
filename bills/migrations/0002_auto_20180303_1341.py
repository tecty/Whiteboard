# Generated by Django 2.0.2 on 2018-03-03 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bills', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='state',
            field=models.CharField(choices=[('PC', 'Processing'), ('PD', 'Pending'), ('FN', 'Finished')], default='PC', max_length=2),
        ),
        migrations.AddField(
            model_name='billtransation',
            name='state',
            field=models.CharField(choices=[('UP', 'Unpaid'), ('SU', 'Suspend-Unpaid'), ('PD', 'Paid'), ('SP', 'Suspend-Paid'), ('DC', 'Decliend')], default='UP', max_length=2),
        ),
        migrations.AlterField(
            model_name='bill',
            name='description',
            field=models.CharField(blank=True, max_length=1023),
        ),
    ]