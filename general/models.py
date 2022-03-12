import uuid
from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=128)
    web_code = models.CharField(max_length=128)
    country_code = models.CharField(max_length=128,blank=True,null=True)
    flag = models.ImageField(upload_to="countries/flags/",blank=True,null=True)
    phone_code = models.CharField(max_length=128,blank=True,null=True)
    is_active = models.BooleanField(default=True)
    phone_number_length = models.PositiveIntegerField(blank=True,null=True)

    class Meta:
        db_table = 'general_country'
        verbose_name ='country'
        verbose_name_plural ='countries'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Mode(models.Model):
    readonly = models.BooleanField(default=False)
    maintenance = models.BooleanField(default=False)
    down = models.BooleanField(default=False)

    class Meta:
        db_table = 'mode'
        verbose_name ='mode'
        verbose_name_plural ='mode'
        ordering = ('id',)

    def __str__(self):
        return str(self.id)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    auto_id = models.PositiveIntegerField(db_index=True,unique=True)
    creator = models.ForeignKey("auth.User", related_name="creator_%(class)s_objects", on_delete=models.CASCADE, null=True, blank=True)
    updater = models.ForeignKey("auth.User", related_name="updator_%(class)s_objects", on_delete=models.CASCADE, null=True, blank=True)
    date_added = models.DateTimeField(db_index=True,auto_now_add=True)
    date_updated = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        abstract = True


class EventCategory(models.Model):
    name = models.CharField(null=True, blank=True, max_length=100)
    published = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Event Categoryntry'
        verbose_name_plural = 'Event Category'