from django.urls import path
from . import views


urlpatterns = [
    path('accounts/login/', views.login_function, name='login'),
    path('signup', views.SignUpFunction.as_view(), name='signup_view'),
    path('accounts/signup/', views.SignUpFunction.as_view(), name='signup'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/reset_password/', views.MyPasswordResetView.as_view(), name='password_reset'),
    path('accounts/personal_info/', views.PersonalInfo.as_view(), name='personal_info'),
    path('accounts/personal_info_edit/', views.PersonalInfo.as_view(), name='personal_info_edit'),
    path('accounts/change-password/', views.change_password, name='change_password'),
    path('access_control', views.access_control_view, name='access_control'),
    path('access_control/grant_staff_permission/<int:user_id>/', views.grant_staff_permission, name='grant_staff_permission'),
    path('access_control/remove_staff_permission/<int:user_id>/', views.remove_staff_permission, name='remove_staff_permission'),
    ]