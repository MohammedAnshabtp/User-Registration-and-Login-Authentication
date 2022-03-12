from accounts.models import  Profile
from django.shortcuts import get_object_or_404


def get_auto_id(model):
    auto_id = 1
    latest_auto_id =  model.objects.all().order_by("-date_added")[:1]
    if latest_auto_id:
        for auto in latest_auto_id:
            auto_id = auto.auto_id + 1
    return auto_id

    
def generate_serializer_errors(args):
    message = ""
    for key, values in args.items():
        error_message = ""
        for value in values:
            error_message += value + ","
        error_message = error_message[:-1]
        message += f"{key} - {error_message} | "
    return message[:-3]


def get_current_profile(request):
    if Profile.objects.filter(user=request.user).exists():

        user_profile = get_object_or_404(Profile, user=request.user)

        print("user_profile-=-=-=-=", user_profile)
       
        title = "Success"

        response_data = {
            "StatusCode": 6000,
            "title": title,
            "user_profile_pk": user_profile.pk,
            "user_profile_data" : {
                "user_profile_pk" : user_profile.pk,
                "name" : user_profile.name,
                "email" : user_profile.email,
                "phone" : user_profile.phone,
                "user_pk" : user_profile.user.pk,
            }
        }
    else:
        response_data = {
            "StatusCode": 6001,
            "data" : {
                "title" : "Failed",
                "message" : "Profile not found",
            }
        }

    return response_data