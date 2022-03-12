from django.urls import path,re_path

from api.v1.accounts import views
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

app_name = "api_v1_accounts"

urlpatterns = [
    path('login/enter',views.enter),
    path('login/enter/otp',views.enter_with_otp),
    path('login/verify',views.verify),
    path('login/verify/otp/',views.verify_otp),
    path('login/resend/otp',views.resend_otp),

    path('signup/enter/phone/', views.signup_enter_phone),
    path('signup/resend/otp/', views.signup_resend_otp),
    path('signup/verify/phone/', views.signup_verify_phone),
    path('signup/set/name',views.signup_set_name),
    path('signup/set/password',views.signup_set_password),

    path('forget/password/enter/phone', views.forget_password_enter_phone),
    path('forget/password/resend/otp', views.resend_otp),
    path('forget/password/verify/phone',views.forget_password_verify_phone),
    path('forget/password/reset', views.forget_password_reset_password),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]