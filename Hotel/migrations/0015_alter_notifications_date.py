# Generated by Django 4.2.6 on 2024-03-04 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Hotel', '0014_alter_hotel_user_notifications_bookmark'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notifications',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]