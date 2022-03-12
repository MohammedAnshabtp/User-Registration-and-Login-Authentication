import base64
import json
from turtle import update

import requests
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings as SETTINGS
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group, User

from general.decorators import check_mode
from .serializers import (PhoneNumberSerializer, OTPSerializer, NameSerializer, PasswordSerializer, UserTokenObtainPairSerializer,ResetPasswordSerializer)
from api.v1.general.functions import generate_serializer_errors
from accounts.models import Profile, TemporaryProfile, OtpRecord
from general.models import Country
from api.v1.accounts.functions import randomnumber, validate_password
from general.functions import generate_unique_id, get_auto_id
from general.encryption import *


@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def enter(request):
    serialized = PhoneNumberSerializer(data=request.data)
    if serialized.is_valid():

        # Getting login details
        country_web_code = request.data['country']
        phone = request.data['phone']
        is_country_ok = False
        is_profile_ok = False
        is_user_ok = False

        if Country.objects.filter(web_code=country_web_code).exists():
            is_country_ok = True

        if Profile.objects.filter(country__web_code=country_web_code, phone=phone).exists():
            is_profile_ok = True

        if is_country_ok and is_profile_ok:

            response_data = {
                "StatusCode": 6000,
                "data": {
                    "title": "Success",
                    "message": "successfull",
                    "country" : country_web_code,
                    "phone" : phone,
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "User Not Exists",
                    "message": "User Not Exists",
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def enter_with_otp(request):
    serialized = PhoneNumberSerializer(data=request.data)
    if serialized.is_valid():

        # Getting login details
        country_web_code = request.data['country']
        phone = request.data['phone']

        is_country_ok = False
        is_profile_ok = False
        is_user_ok = False
        phone_code = None
        Phone_with_code = None
        user = None
        profile = None
        country = None

        if Country.objects.filter(web_code=country_web_code).exists():
            country = Country.objects.get(web_code=country_web_code)
            phone_code = country.phone_code
            is_country_ok = True

        if Profile.objects.filter(country=country, phone=phone).exists():
            profile = Profile.objects.get(country=country, phone=phone)
            is_profile_ok = True

        if is_country_ok and is_profile_ok:
            otp_record = None
            phone_with_code = f'+{phone_code}{phone}'
            
            if OtpRecord.objects.filter(phone=phone, country=country, is_applied=False).exists():
                otp_record = OtpRecord.objects.filter(phone=phone,country=country, is_applied=False).latest("date_added")
                if otp_record.attempts <= 3:
                    # Set attempts
                    otp_record.attempts += 1
                    otp_record.date_updated = timezone.now()
                    otp_record.save()

                    #Set profle instance
                    profile.otp_number = otp_record.otp
                    profile.save()
                    response_data = {
                        "StatusCode": 6000,
                        "data": {
                            "country" : country_web_code,
                            "phone" : phone,
                            "title": "Success",
                            "message": "successfull",
                        }
                    } 
                else:
                    time_limit = otp_record.date_updated + timezone.timedelta(minutes=15)
                    if time_limit <= timezone.now():
                        #Generate OTP
                        otp = randomnumber(4)

                        #Set OTP Record instance
                        otp_record = OtpRecord.objects.create(
                            country = country,
                            phone = phone,
                            country_id = country.id,
                            otp = otp,
                        )

                        #Set profle instance
                        profile.otp_number = otp_record.otp
                        profile.save()
                        response_data = {
                            "StatusCode": 6000,
                            "data": {
                                "title": "Success",
                                "message": "successfull",
                                "country" : country_web_code,
                                "phone" : phone,
                            }
                        } 
                    else:
                        response_data = {
                            "StatusCode": 6001,
                            "data": {
                                "title": "Failed!",
                                "message": "You crossed the maximum limit of OTPs."
                            }
                        }
            else:
                #Generate OTP
                otp = randomnumber(4)

                #Set OTP Record instance
                otp_record = OtpRecord.objects.create(
                    country = country,
                    phone = phone,
                    country_id = country.id,
                    otp = otp,
                )

                #Set profle instance
                profile.otp_number = otp_record.otp
                profile.save()
                response_data = {
                    "StatusCode": 6000,
                    "data": {
                        "title": "Success",
                        "message": "successfull",
                        "country" : country_web_code,
                        "phone" : phone,
                    }
                }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "User Not Exists",
                    "message": "User Not Exists"
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)
    else:

        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def verify(request):
    serialized = PasswordSerializer(data=request.data)
    if serialized.is_valid():

        # Getting login details
        password = request.data['password']
        phone = request.data['phone']
        country_web_code = request.data['country']       
        
        if Country.objects.filter(web_code=country_web_code, is_active=True).exists():
            country = Country.objects.get(web_code=country_web_code, is_active=True)
            if Profile.objects.filter(phone=phone, country=country, is_verified=True).exists():
                profile = Profile.objects.get(phone=phone, country=country, is_verified=True)
                
                if decrypt(profile.password) == password:
                    
                    headers = {
                        "Content-Type" : "application/json"
                    }

                    data = {
                        "username" : profile.user.username,
                        "password" : password,
                    }

                    protocol = "http://"
                    if request.is_secure():
                        protocol = "https://"

                    host = request.get_host()

                    url = protocol + host + "/api/v1/accounts/token/"
                    
                    response = requests.post(url, headers=headers, data=json.dumps(data))

                    if response.status_code == 200:

                        response_data = {
                            "StatusCode" : 6000,
                            "data": {
                                "title" : "Success",
                                "message" : "successfull",
                                "response" : response.json(),
                                "phone" : phone,
                                "name" : profile.name,
                            }
                        }
                    else:
                        response_data = {
                            "StatusCode": 6001,
                            "data": {
                                "title": "Failed",
                                "message": "Incorrect Password"
                            }
                        } 
                else:
                    response_data = {
                        "StatusCode": 6001,
                        "data": {
                            "title": "Failed",
                            "message": "Incorrect Password"
                        }
                    }    
            else:
                response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "User Not Exists",
                        "message": "User Not Exists"
                    }
                }
        else:
            response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "Service Not Avalilable",
                        "message" : "Service not available in this country"
                    }
                }
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def verify_otp(request):
    is_free_course_enrolled = False
    serialized = OTPSerializer(data=request.data)
    if serialized.is_valid():

        # Getting login details
        otp = request.data['otp']
        phone = request.data['phone']
        country_web_code = request.data['country']
        profile = None

        if Country.objects.filter(web_code=country_web_code, is_active=True).exists():
            country = Country.objects.get(web_code=country_web_code, is_active=True)

        if OtpRecord.objects.filter(phone=phone, country=country, otp=otp, is_applied=False).exists():
            otp_record = OtpRecord.objects.get(phone=phone, country=country, otp=otp, is_applied=False)
            
            if otp_record.attempts <= 3:
                otp_record.is_applied = True
                otp_record.date_updated = timezone.now()
                otp_record.save()

                if Profile.objects.filter(phone=phone,country=country, otp_number=otp, is_verified=True).exists():
                    profile = Profile.objects.get(phone=phone, country=country, otp_number=otp, is_verified=True)

                    headers = {
                        "Content-Type" : "application/json"
                    }

                    data = {
                        "username" : profile.user.username,
                        "password" : decrypt(profile.password),
                    }

                    protocol = "http://"
                    if request.is_secure():
                        protocol = "https://"

                    host = request.get_host()

                    url = protocol + host + "/api/v1/accounts/token/"
                    
                    response = requests.post(url, headers=headers, data=json.dumps(data))

                    if response.status_code == 200:

                        response_data = {
                            "StatusCode" : 6000,
                            "data": {
                                "response" : response.json(),
                                "phone" : phone,
                                "name" : profile.name,
                                "title" : "Success",
                                "message" : "successfull",
                            }
                        } 
                        
                        return Response(response_data, status=status.HTTP_200_OK)

                else:
                    response_data = {
                        "StatusCode": 6001,
                        "data": {
                            "title": "Service not available",
                            "message": "Service Not Available"
                        }
                    }  
            else:
                response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "Failed!",
                        "message": "You crossed the maximum limit of OTPs."
                    }
                }
        else:
            if OtpRecord.objects.filter(phone=phone, country=country, is_applied=False).exists():
                otp_record = OtpRecord.objects.get(phone=phone, country=country, is_applied=False)

                # Set attempts
                otp_record.attempts += 1
                otp_record.date_updated = timezone.now()
                otp_record.save()

            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "OTP not exists",
                    "message": "Please try again"
                }
            }
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }
        
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def resend_otp(request):
    serialized = PhoneNumberSerializer(data=request.data)
    if serialized.is_valid():

        # Getting login details
        country_web_code = request.data['country']
        phone = request.data['phone']

        is_country_ok = False
        is_profile_ok = False
        country = None
        phone_code = None
        phone_with_code = None
        profile = None

        if Country.objects.filter(web_code=country_web_code).exists():
            phone_code = Country.objects.get(web_code=country_web_code).phone_code
            country = Country.objects.get(web_code=country_web_code).pk
            is_country_ok = True

        if Profile.objects.filter(country__web_code=country_web_code, phone=phone).exists():
            profile = Profile.objects.get(country__web_code=country_web_code, phone=phone) 
            is_profile_ok = True

        if is_country_ok and is_profile_ok:
            otp_record = None
            phone_with_code = f'+{phone_code}{phone}'

            if OtpRecord.objects.filter(phone=phone, otp=profile.otp_number, country=country, is_applied=False).exists():
                otp_record = OtpRecord.objects.filter(phone=phone,  otp=profile.otp_number, country=country, is_applied=False).latest("date_added")
                if otp_record.attempts <= 3:

                    # Set attempts
                    otp_record.attempts += 1
                    otp_record.date_updated = timezone.now()
                    otp_record.save()
                    response_data = {
                        "StatusCode": 6000,
                        "data": {
                            "title": "Success",
                            "message": "successfull",
                            "country" : country_web_code,
                            "phone" : phone,
                        }
                    }
                else:
                    time_limit = otp_record.date_updated + timezone.timedelta(minutes=15)
                    if time_limit <= timezone.now():
                        #Generate OTP
                        otp = randomnumber(4)

                        #Set OTP Record instance
                        otp_record = OtpRecord.objects.create(
                            country = country,
                            phone = phone,
                            country_id = country.id,
                            otp = otp,
                        )

                        #Set profle instance
                        profile.otp_number = otp_record.otp
                        profile.save()
                        response_data = {
                            "StatusCode": 6000,
                            "data": {
                                "title": "Success",
                                "message": "successfull",
                                "country" : country_web_code,
                                "phone" : phone,
                            }
                        } 
                    else:
                        response_data = {
                            "StatusCode": 6001,
                            "data": {
                                "title": "Failed!",
                                "message": "You crossed the maximum limit of OTPs."
                            }
                        }
            else:
                response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "OTP not exists",
                        "message": "Please try again"
                    }
                }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "User Not Exists",
                    "message": "User Not Exists"
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            } 
        }

        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def signup_enter_phone(request):
    serialized = PhoneNumberSerializer(data=request.data)
    if serialized.is_valid():

        # Getting login details
        country_web_code = request.data['country']
        phone = request.data['phone']

        is_country_ok = False
        is_phone_ok = False
        phone_code = None
        phone_with_code = None
        country = None
        message = ""

        #Check profile instance
        if not Profile.objects.filter(country__web_code=country_web_code, phone=phone).exists():

            #Check country
            if Country.objects.filter(web_code=country_web_code).exists():
                country = Country.objects.get(web_code=country_web_code)
                is_country_ok = True
            else:
                message = "Service not available in this country"

            #Check Phone 
            if is_country_ok:
                if len(phone) == country.phone_number_length:
                    is_phone_ok = True
                else:
                    message = "Invalid phone number"

            if is_country_ok and is_phone_ok:
                #Generate OTP
                otp = randomnumber(4)

                #Set user temporary profle instance
                temporary_profile = TemporaryProfile.objects.create(
                    phone = phone,
                    country_pk = country.pk,
                    otp_number = otp,
                    is_verified = False
                )

                phone_code = country.phone_code
                phone_with_code = f'+{phone_code}{phone}'

                otp_record = None
                if OtpRecord.objects.filter(phone=phone,country=country, is_applied=False).exists():
                    otp_record = OtpRecord.objects.filter(phone=phone,country=country, is_applied=False).latest("date_added")
                    phone_code = country.phone_code
                    phone_with_code = f'+{phone_code}{phone}'
                    if otp_record.attempts <= 3:
                        # Set attempts
                        otp_record.attempts += 1
                        otp_record.date_updated = timezone.now()
                        otp_record.save()

                        #Set profle instance
                        temporary_profile.otp_number = otp_record.otp
                        temporary_profile.save()

                        #send sms
                        message = "Talrop : %s is your verification code. Please do not reveal it to anyone." %(otp_record.otp)
                        if not SETTINGS.DEBUG:
                            if country_web_code == 'IN':
                                send_quick_fast2sms(phone, otp_record.otp) 
                            else:
                                send_twilio_sms(phone_with_code, message)

                        response_data = {
                            "StatusCode": 6000,
                            "data": {
                                "title": "Success",
                                "message": "successfull",
                                "country" : country_web_code,
                                "phone" : phone,

                            }
                        } 
                    else:
                        time_limit = otp_record.date_updated + timezone.timedelta(minutes=15)
                        if time_limit <= timezone.now():
                            #Generate OTP
                            otp = randomnumber(4)

                            #Set OTP Record instance
                            otp_record = OtpRecord.objects.create(
                                country = country,
                                phone = phone,
                                country_id = country.id,
                                otp = otp,
                            )

                            #Set profle instance
                            temporary_profile.otp_number = otp_record.otp
                            temporary_profile.save()

                            #send sms
                            message = "Talrop : %s is your verification code. Please do not reveal it to anyone." %(otp)
                            if not SETTINGS.DEBUG:
                                if country_web_code == 'IN':
                                    send_quick_fast2sms(phone, otp) 
                                else:
                                    send_twilio_sms(phone_with_code, message)

                            response_data = {
                                "StatusCode": 6000,
                                "data": {
                                    "title": "Success",
                                    "message": "successfull",
                                    "country" : country_web_code,
                                    "phone" : phone,
                                }
                            } 
                        else:
                            response_data = {
                                "StatusCode": 6001,
                                "data": {
                                    "title": "Failed!",
                                    "message": "You crossed the maximum limit of OTPs."
                                }
                            }
                else:
                    #send sms
                    message = "Talrop : %s is your verification code. Please do not reveal it to anyone." %(otp)
                    if not SETTINGS.DEBUG:
                        if country_web_code == 'IN':
                            send_quick_fast2sms(phone, message) 
                        else:
                            send_twilio_sms(phone_with_code, message)

                    #Set OTP Record instance
                    OtpRecord.objects.create(
                        country=country,
                        phone = phone,
                        otp = otp,
                        country_id = country.id
                    )

                    response_data = {
                        "StatusCode": 6000,
                        "data": {
                            "title": "Success",
                            "message": "successfull",
                            "country" : country_web_code,
                            "phone" : phone,
                        }
                    } 
            else:
                response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "An error occured",
                        "message": message
                    }
                }
        else:
            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "An error occured",
                    "message": "User with this phone already exists."
                }
            }

        return Response(response_data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def signup_resend_otp(request):
    serialized = PhoneNumberSerializer(data=request.data)
    if serialized.is_valid():

        # Getting login details
        country_web_code = request.data['country']
        phone = request.data['phone']
        is_country_ok = False
        is_profile_ok = False
        phone_code = None
        phone_with_code = None
        user = None
        profile = None

        if Country.objects.filter(web_code=country_web_code,is_active=True).exists():
            country = Country.objects.get(web_code=country_web_code,is_active=True)
            is_country_ok = True

        if TemporaryProfile.objects.filter(country_pk=country.pk, phone=phone, is_verified = False).exists():
            temporary_profile = TemporaryProfile.objects.filter(country_pk=country.pk, phone=phone, is_verified = False).latest("date_added")
            is_profile_ok = True

        if is_country_ok and is_profile_ok:
            otp_record = None
            phone_code = country.phone_code
            phone_with_code = f'+{phone_code}{phone}'
            if OtpRecord.objects.filter(phone=phone,country=country, is_applied=False).exists():
                otp_record = OtpRecord.objects.filter(phone=phone,country=country, is_applied=False).latest("date_added")
                
                if otp_record.attempts <= 3:

                    if otp_record.otp == temporary_profile.otp_number:
                        #send sms
                        message = "Talrop : %s is your verification code. Please do not reveal it to anyone." %(otp_record.otp)
                        if not SETTINGS.DEBUG:
                            if country_web_code == 'IN':
                                send_quick_fast2sms(phone, otp_record.otp) 
                            else:
                                send_twilio_sms(phone_with_code, message)

                        # Set attempts
                        otp_record.attempts += 1
                        otp_record.save()  

                        response_data = {
                            "StatusCode": 6000,
                            "data": {
                                "title": "Success",
                                "message": "successfull",
                                "country" : country_web_code,
                                "phone" : phone,
                            }
                        }
                    else:
                        response_data = {
                            "StatusCode": 6001,
                            "data": {
                                "title": "Failed",
                                "message": "Please try again"
                            }
                        }
                else:
                    time_limit = otp_record.date_updated + timezone.timedelta(minutes=15)
                    if time_limit <= timezone.now():
                        #Generate OTP
                        otp = randomnumber(4)

                        #Set OTP Record instance
                        otp_record = OtpRecord.objects.create(
                            country = country,
                            phone = phone,
                            country_id = country.id,
                            otp = otp,
                        )

                        #Set profle instance
                        profile.otp_number = otp_record.otp
                        profile.save()
                        response_data = {
                            "StatusCode": 6000,
                            "data": {
                                "title": "Success",
                                "message": "successfull",
                                "country" : country_web_code,
                                "phone" : phone,
                            }
                        } 
                    else:
                        response_data = {
                            "StatusCode": 6001,
                            "data": {
                                "title": "Failed!",
                                "message": "You crossed the maximum limit of OTPs."
                            }
                        }
            else:
                response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "Failed",
                        "message": "Please try again"
                    }
                }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "Failed",
                    "message": "User Not Exists"
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)
    else:

        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            } 
        }

        return Response(response_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def signup_verify_phone(request):
    serialized = OTPSerializer(data=request.data)

    if serialized.is_valid():
        # Getting login details
        phone = request.data['phone']
        otp = request.data['otp']
        country_web_code = request.data['country']

        message = ""
        response_data = {}
        is_country_ok = False
        country = None

        #Check country
        if Country.objects.filter(web_code=country_web_code,is_active=True).exists():
            country = Country.objects.get(web_code=country_web_code,is_active=True)
            is_country_ok = True
        else:
            message = "Service not available in this country"

        if is_country_ok:
            if TemporaryProfile.objects.filter(phone=phone,country_pk=country.pk, otp_number=otp, is_verified=False).exists():      
                temporary_profile = TemporaryProfile.objects.filter(phone=phone, country_pk=country.pk, otp_number=otp, is_verified=False).latest("date_added")     
                otp_record = None
                if OtpRecord.objects.filter(phone=phone,country=country, otp=otp, is_applied=False).exists():
                    otp_record = OtpRecord.objects.get(phone = phone,country=country, otp=otp, is_applied=False)

                    temporary_profile.is_verified = True
                    temporary_profile.save()

                    #Update OTP record instance
                    otp_record.is_applied = True
                    otp_record.date_updated = timezone.now()
                    otp_record.save()

                    response_data = {
                        "StatusCode": 6000,
                        "data": {
                            "phone" : phone,
                            "title": "Successfull",
                            "message": "Phone number verified successfully",
                        }
                    }
                else:
                    response_data = {
                        "StatusCode": 6001,
                        "data": {
                            "title": "Failed",
                            "message": "OTP not found",
                        }
                    }

            elif TemporaryProfile.objects.filter(phone=phone, country_pk=country.pk, otp_number=otp, is_verified=True).exists():
                response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "Failed",
                        "message": "Already verified",
                    }
                }
            else:
                if OtpRecord.objects.filter(phone=phone, country=country, is_applied=False).exists():
                    otp_record = OtpRecord.objects.get(phone=phone, country=country, is_applied=False)

                    # Set attempts
                    otp_record.attempts += 1
                    otp_record.date_updated = timezone.now()
                    otp_record.save()
                    
                response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "An error occured",
                        "message" : "Invalid OTP!"
                    }
                }
        else:
            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "An error occured",
                    "message": "Service not available"
                }
            }
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def signup_set_name(request):
    serialized = NameSerializer(data=request.data)

    if serialized.is_valid():
        # Getting login details
        phone = request.data['phone']
        name = request.data['name']
        country_web_code = request.data['country']

        message = ""
        is_country_ok = False
        response_data = {}

        if Country.objects.filter(web_code=country_web_code,is_active=True).exists():
            country = Country.objects.get(web_code=country_web_code,is_active=True)
            is_country_ok = True
            if TemporaryProfile.objects.filter(phone=phone,country_pk=country.pk, is_verified=True).exists():
                temporary_profile = TemporaryProfile.objects.filter(phone=phone,country_pk=country.pk, is_verified=True).latest("date_added")
                
                #Update profile instance
                temporary_profile.name = name
                temporary_profile.save()
                
                response_data = {
                    "StatusCode": 6000,
                    "data": {
                        "title": "Successfull",
                        "message": "Name updated successfully",
                        "phone" : phone,
                        "name" : name,
                    }
                }
            else:
                response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "Failed",
                        "message": "Profile not found",
                    }
                }
            
        else:
            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "An error occured",
                    "message": "Service not available"
                }
            }

        return Response(response_data, status=status.HTTP_200_OK)
        
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def signup_set_password(request):
    serialized = PasswordSerializer(data=request.data)

    if serialized.is_valid():
        # Getting login details
        phone = request.data['phone']
        password = request.data['password']
        country_web_code = request.data['country']

        message = ""
        is_country_ok = False
        response_data = {}

        if Country.objects.filter(web_code=country_web_code, is_active=True).exists():
            country = Country.objects.get(web_code=country_web_code, is_active=True)
            
            is_country_ok = True
            
            if TemporaryProfile.objects.filter(phone=phone, country_pk=country.pk, is_verified=True).exists():
                temporary_profile = TemporaryProfile.objects.filter(phone=phone, country_pk=country.pk, is_verified=True).latest("date_added")
                validate_password_response = validate_password(password)
                if validate_password_response["status"] == True:

                    country_pk = temporary_profile.country_pk
                    country = get_object_or_404(Country, pk=country_pk)

                    #Create user object
                    complete_username = generate_unique_id(size=20)

                    username_duplicate = User.objects.filter(username=complete_username).exists()
                    
                    while username_duplicate:
                        complete_username = generate_unique_id(size=20)
                        username_duplicate = User.objects.filter(username=complete_username).exists()

                    user = User.objects.create_user(
                        username=complete_username,
                        password=password
                    )

                    # Encrypt password
                    encrypted_password = encrypt(password)

                    profile = Profile.objects.create(
                        auto_id = get_auto_id(Profile),
                        creator = user,
                        updater = user,

                        user = user,
                        name = temporary_profile.name,
                        phone = temporary_profile.phone,
                        country = country,
                        otp_number = temporary_profile.otp_number,
                        password = encrypted_password,
                        is_verified = temporary_profile.is_verified,
                    )
                    
                    person_group, created = Group.objects.get_or_create(name='person')
                    person_group.user_set.add(user)

                    headers = {
                        "Content-Type" : "application/json"
                    }

                    data = {
                        "username" : complete_username,
                        "password" : password,
                    }

                    protocol = "http://"
                    if request.is_secure():
                        protocol = "https://"

                    host = request.get_host()

                    url = protocol + host + "/api/v1/accounts/token/"
                    
                    response = requests.post(url, headers=headers, data=json.dumps(data))

                    if response.status_code == 200:
                        temporary_profile.delete()
                        
                        response_data = {
                            "StatusCode": 6000,
                            "data": {
                                "title": "Successful",
                                "student_token" : response.json(),
                            }
                        }
                    else:
                        response_data = {
                            "StatusCode" : 6001,
                            "data": {
                                "title" : "Failed",
                                "message" : "An error occurred"
                            }
                        }
                else:
                    response_data = {
                        "StatusCode": 6001,
                        "data" : {
                            "title": "An error occured",
                            "message" : validate_password_response["message"]
                        },
                    }
            else:
                response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "Failed",
                        "message": "An error occured",
                    }
                }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "Failed",
                    "message": "Service not Available in this Country",
                }
            } 
    
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def forget_password_enter_phone(request):
    serialized = PhoneNumberSerializer(data=request.data)
    if serialized.is_valid():

        # Getting login details
        country_web_code = request.data['country']
        phone = request.data['phone']

        is_country_ok = False
        is_phone_ok = False
        phone_code = None
        phone_with_code = None
        country = None
        message = ""

        #Check profile instance
        if Profile.objects.filter(country__web_code=country_web_code, phone=phone).exists():
            profile = Profile.objects.get(country__web_code=country_web_code, phone=phone)

            #Check country
            if Country.objects.filter(web_code=country_web_code).exists():
                country = Country.objects.get(web_code=country_web_code)
                is_country_ok = True
            else:
                message = "Service not available in this country"
            #Check Phone 
            if is_country_ok:
                if len(phone) == country.phone_number_length:
                    is_phone_ok = True
                else:
                    message = "Invalid phone number"
            else:
                message = "Invalid Country"

            if is_country_ok and is_phone_ok:
                is_max_attempted = False
                otp_record = None
                otp = 0
                if OtpRecord.objects.filter(phone=phone, country=country, is_applied=False).exists():
                    otp_record = OtpRecord.objects.filter(phone=phone, country=country, is_applied=False).latest("date_added")
                    otp = otp_record.otp
                    phone_code = country.phone_code
                    phone_with_code = f'+{phone_code}{phone}'

                    if otp_record.attempts <= 3:
                        # Set attempts
                        otp_record.attempts += 1
                        otp_record.save()
                    else:
                        time_limit = otp_record.date_updated + timezone.timedelta(days=1)
                        if time_limit <= timezone.now():
                            #Generate OTP
                            otp = randomnumber(4)

                            #Set OTP Record instance
                            otp_record = OtpRecord.objects.create(
                                country = country,
                                phone = phone,
                                country_id = country.id,
                                otp = otp,
                            )

                            #Set profle instance
                            profile.otp_number = otp_record.otp
                            profile.save()

                            #send sms
                            message = "Talrop : %s is your verification code. Please do not reveal it to anyone." %(otp)
                            if not SETTINGS.DEBUG:
                                if country_web_code == 'IN':
                                    send_quick_fast2sms(phone, otp) 
                                else:
                                    send_twilio_sms(phone_with_code, message)

                            response_data = {
                                "StatusCode": 6000,
                                "country" : country_web_code,
                                "phone" : phone,
                                "title": "Success",
                                "message": "successfull",
                            } 
                        else:
                            is_max_attempted = True
                else:
                    #Generate OTP
                    otp = randomnumber(4)

                    #Set OTP Record instance
                    otp_record = OtpRecord.objects.create(
                        country = country,
                        phone = phone,
                        otp = otp,
                        country_id = country.id
                    )
                
                profile.otp_number = otp
                profile.save()

                #send sms
                message = "Talrop : %s is your verification code. Please do not reveal it to anyone." %(otp)
                if not SETTINGS.DEBUG:
                    if country_web_code == 'IN':
                        send_quick_fast2sms(phone, otp) 
                    else:
                        send_twilio_sms(phone_with_code, message)

                if not is_max_attempted:
                    response_data = {
                        "StatusCode": 6000,
                        "data": {
                            "title": "Success",
                            "message": "Successfull",
                            "country" : country_web_code,
                            "phone" : phone,
                        }
                    }
                else:
                    response_data = {
                        "StatusCode": 6001,
                        "data": {
                            "title": "Failed!",
                            "message": "You crossed the maximum limit of OTPs."
                        }
                    }
            else:
                response_data = {
                    "StatusCode": 6001,
                    "data": {
                        "title": "An error occured",
                        "message": message
                    }
                }
        else:
            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "An error occured",
                    "message": "User with this phone not exists."
                }
            }

        return Response(response_data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@check_mode
def forget_password_verify_phone(request):
    serialized = OTPSerializer(data=request.data)
    if serialized.is_valid():

        # Getting login details
        otp = request.data['otp']
        phone = request.data['phone']
        country_web_code = request.data['country']

        is_country_ok = False
        is_profile_ok = False
        is_user_ok = False
        user = None
        profile = None
        
        if Country.objects.filter(web_code=country_web_code).exists():
            country = Country.objects.get(web_code=country_web_code)
            is_country_ok = True 
            if Profile.objects.filter(phone=phone,country=country, otp_number=otp, is_verified=True).exists():
                profile = Profile.objects.get(phone=phone,country=country, otp_number=otp, is_verified=True)
                is_profile_ok = True

                otp_record = None
                response_data = {}
                if OtpRecord.objects.filter(phone=phone, country=country, otp=otp, is_applied=False).exists():
                    otp_record = OtpRecord.objects.get(phone=phone, country=country, otp=otp, is_applied=False)

                    if otp_record.attempts <= 3:
                        otp_record.is_applied = True
                        otp_record.date_updated = timezone.now()
                        otp_record.save()

                        if Profile.objects.filter(phone=phone,country=country, otp_number=otp, is_verified=True).exists():
                            profile = Profile.objects.get(phone=phone,country=country, otp_number=otp, is_verified=True)
                            is_profile_ok = True

                            headers = {
                                "Content-Type" : "application/json"
                            }

                            data = {
                                "username" : profile.user.username,
                                "password" : decrypt(profile.password),
                            }

                            protocol = "http://"
                            if request.is_secure():
                                protocol = "https://"

                            host = request.get_host()

                            url = protocol + host + "/api/v1/accounts/token/"
                            
                            response = requests.post(url, headers=headers, data=json.dumps(data))

                            if response.status_code == 200:

                                response_data = {
                                    "StatusCode" : 6000,
                                    "data": {
                                        "title" : "Success",
                                        "message" : "successfull",
                                        "response" : response.json(),
                                        "phone" : phone,
                                        "name" : profile.name,
                                    }
                                }
                                
                                return Response(response_data, status=status.HTTP_200_OK)
                                
                        else:
                            response_data = {
                                "StatusCode": 6001,
                                "title": "Service not available",
                                "message": "Service Not Available"
                            }

                    else:
                        response_data = {
                            "StatusCode": 6001,
                            "title": "Failed!",
                            "message": "You crossed the maximum limit of OTPs."
                        }
                else:
                    if OtpRecord.objects.filter(phone=phone, country=country, is_applied=False).exists():
                        otp_record = OtpRecord.objects.get(phone=phone, country=country, is_applied=False)

                        # Set attempts
                        otp_record.attempts += 1
                        otp_record.date_updated = timezone.now()
                        otp_record.save()

                    response_data = {
                        "StatusCode": 6001,
                        "data": {
                            "title": "Failed",
                            "message": "Invalid OTP"
                        }
                    }

                return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                "StatusCode": 6001,
                "data": {
                    "title": "Failed",
                    "message": "Service Not Avalilable in this Country!"
                }
            }
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@check_mode
def forget_password_reset_password(request):
    serialized = ResetPasswordSerializer(data=request.data)

    if serialized.is_valid():
        # Getting login details
        password = request.data['password']

        message = ""
        response_data = {}

        validate_password_response = validate_password(password)
        if validate_password_response["status"] == True:
            if Profile.objects.filter(user=request.user, is_verified=True).exists():
                profile = Profile.objects.get(user=request.user, is_verified=True)
                # Encrypt password
                encrypted_password = encrypt(password)

                user = profile.user
                user.set_password(password)
                user.save()

                profile.password = encrypted_password
                profile.is_profile_updated = True
                profile.save()

                response_data = {
                    "StatusCode": 6000,
                    "data": {
                        "title": "Successfull",
                        "message": "Password updated successfully",
                        "phone" : profile.phone,
                    }
                }

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                message = "Profile not exists"
        else:
            message = validate_password_response["message"]

        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "An error occured",
                "message": message
            }
        }
    
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "StatusCode": 6001,
            "data": {
                "title": "Validation Error",
                "message": generate_serializer_errors(serialized._errors)
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)













