# Generated by Django 4.2.6 on 2024-03-06 06:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Hotel', '0005_remove_booking_booking_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='date_of_booking',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]