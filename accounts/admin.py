from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from accounts.models import ChiefProfile, OtpRecord, Profile, TemporaryProfile


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    ordering = ('pk',)
    list_display = ('pk', 'username', 'email', 'first_name', 'last_name', 'is_staff',)
    search_fields = ('username', 'pk')

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('pk', 'date_added', 'name','phone','email','country','otp_number','is_verified', 'password', 'gender', 'dob')
    ordering = ('-date_added',)
    search_fields = ('phone', 'pk', 'name')
admin.site.register(Profile,ProfileAdmin)


class OtpRecordAdmin(admin.ModelAdmin):
    list_display = ('pk', 'date_added', 'phone', 'otp', 'attempts', 'is_applied')
    ordering = ('-date_added',)
    search_fields = ('phone', )

admin.site.register(OtpRecord,OtpRecordAdmin)


class TemporaryProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'is_verified')
    search_fields = ('phone', )

admin.site.register(TemporaryProfile, TemporaryProfileAdmin)


class ChiefProfileAdmin(admin.ModelAdmin):
    list_display = ('auto_id', 'username', 'password')
    exclude = ('auto_id', 'creator', 'updater', 'is_deleted', 'password', 'user')
    search_fields = ('user', )

admin.site.register(ChiefProfile, ChiefProfileAdmin)