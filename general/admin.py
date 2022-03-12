from django.contrib import admin

from general.models import Country,Mode

class CountryAdmin(admin.ModelAdmin):
    list_display = ('name','web_code','flag','phone_code','phone_number_length')
    search_fields = ('name', 'web_code')
admin.site.register(Country,CountryAdmin)


class ModeAdmin(admin.ModelAdmin):
    list_display = ('down', 'maintenance', 'readonly')
admin.site.register(Mode,ModeAdmin)