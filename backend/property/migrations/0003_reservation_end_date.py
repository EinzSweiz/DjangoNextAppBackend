# Generated by Django 5.1.3 on 2024-11-15 12:12

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('property', '0002_reservation'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='end_date',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
