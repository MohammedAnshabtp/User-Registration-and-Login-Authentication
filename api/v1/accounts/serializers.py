import profile
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from accounts.models import Profile


class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super(UserTokenObtainPairSerializer, cls).get_token(user)
        return token

    def validate(cls, attrs):
        data = super(UserTokenObtainPairSerializer, cls).validate(attrs)

        refresh = cls.get_token(cls.user)

        print(dir(refresh))

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        roles = list(set([x.name for x in cls.user.groups.all()]))
        if 'app_user' in roles:
            data['role'] = "app_user"
        
        elif cls.user.is_superuser:
            data['role'] = "superuser"
        else:
            data['role'] = "user"

        return data

    
class PhoneNumberSerializer(serializers.Serializer):
    country = serializers.CharField()
    phone = serializers.CharField()


class OTPSerializer(serializers.Serializer):
    country = serializers.CharField()
    phone = serializers.CharField(max_length=16)
    otp = serializers.IntegerField()

class NameSerializer(serializers.Serializer):
    name = serializers.CharField()
    country = serializers.CharField()
    phone = serializers.CharField(max_length=16)

class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    country = serializers.CharField()
    phone = serializers.CharField(max_length=16)

class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()    

