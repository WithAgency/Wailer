# Generated by Django 4.0.1 on 2022-01-31 22:34

import uuid

import phonenumber_field.modelfields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Email",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                ("data", models.JSONField()),
                ("type", models.CharField(max_length=1000)),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                ("date_sent", models.DateTimeField(blank=True, null=True)),
                ("sender", models.EmailField(max_length=1000)),
                ("recipient", models.EmailField(max_length=1000)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Sms",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                ("data", models.JSONField()),
                ("type", models.CharField(max_length=1000)),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                ("date_sent", models.DateTimeField(blank=True, null=True)),
                (
                    "sender",
                    phonenumber_field.modelfields.PhoneNumberField(
                        max_length=128, region=None
                    ),
                ),
                (
                    "recipient",
                    phonenumber_field.modelfields.PhoneNumberField(
                        max_length=128, region=None
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
