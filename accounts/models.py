import os
import uuid
from datetime import datetime

import requests
from django.conf import settings as SETTINGS
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.fields import SlugField
from versatileimagefield.fields import VersatileImageField

from general.encryption import *
from general.functions import get_auto_id
from general.middlewares import RequestMiddleware
from general.models import BaseModel

PROFILE_GENDER_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),
    ('others', 'Others'),
)


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_added = models.DateTimeField(db_index=True, auto_now_add=True)
    
    user = models.OneToOneField("auth.User",on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField(max_length=128, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    photo = VersatileImageField(upload_to="profile/",blank=True,null=True)
    country = models.ForeignKey('general.Country', on_delete=models.CASCADE)
    password = models.TextField(blank=True, null=True)
    
    otp_number = models.PositiveIntegerField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_profile_updated = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    
    gender = models.CharField(max_length=128, choices=PROFILE_GENDER_CHOICES, null=True, blank=True)
    dob = models.DateField(blank=True, null=True)
    
  

    class Meta:
        db_table = 'users_profile'
        verbose_name ='profile'
        verbose_name_plural ='profiles'
        ordering = ('name',)
        
    def __str__(self):
        if self.name:
            return self.name
        else:
            return self.phone


class OtpRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=16)
    otp = models.PositiveIntegerField()
    attempts = models.PositiveIntegerField(default=1)
    is_applied = models.BooleanField(default=False)
    country = models.ForeignKey('general.Country', on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(db_index=True, auto_now_add=True)
    date_updated = models.DateTimeField(db_index=True, auto_now_add=True)

    class Meta:
        db_table = 'users_otp_record'
        verbose_name ='Otp Record'
        verbose_name_plural ='Otp Records'
        ordering = ('-date_added',)
        
    def __str__(self):
        return self.phone

class TemporaryProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_added = models.DateTimeField(db_index=True, auto_now_add=True)
    name = models.CharField(max_length=128, blank=True, null=True)
    country_pk = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField(max_length=128, blank=True, null=True)
    otp_number = models.PositiveIntegerField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    gender = models.CharField(max_length=128, choices=PROFILE_GENDER_CHOICES, null=True)
    dob = models.DateField(default=datetime.now, null=True)
   
    class Meta:
        db_table = 'users_temporary_profile'
        verbose_name ='Temporary profile'
        verbose_name_plural ='Temporary profiles'
        ordering = ('name',)
        
    def __str__(self):
        if self.name:
            return self.name
        else:
            return self.phone


class ChiefProfile(BaseModel):
    username = models.CharField(max_length=128)
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    password = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.creator:
            # First we need create an instance of that and later get the current_request assigned
            request = RequestMiddleware(get_response=None)
            request = request.thread_local.current_request

            if self._state.adding:
                auto_id = get_auto_id(ChiefProfile)

                chief_username = self.username
                password = User.objects.make_random_password(length=12, allowed_chars="abcdefghjkmnpqrstuvwzyx#@*%$ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
                chief_email = f"{chief_username}@talrop.com"

                user = User.objects.create_user(
                    username=chief_username,
                    email=chief_email,
                    password=password
                )

                chief_group, created = Group.objects.get_or_create(name='students_relations_officer')
                chief_group.user_set.add(user)

                self.creator = request.user
                self.updater = request.user
                self.auto_id = auto_id
                self.user = user
                self.password = encrypt(password)

        super(ChiefProfile, self).save(*args, **kwargs)

    class Meta:
        db_table = 'users_chief_profile'
        verbose_name = 'chief profile'
        verbose_name_plural = 'chief profiles'
        ordering = ('auto_id',)