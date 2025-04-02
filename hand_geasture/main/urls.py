from django.urls import path
from .views import *

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path("", home, name="home"),
    path("accounts/", accounts_view, name="accounts"),
    path("user/<int:user_id>/", user_detail_view, name="user_detail"),
    path("patients/", patients_view, name="patients"),
    path("patient/<int:patient_id>/", patient_detail_view, name="patient_detail"),
]   

# AJAX URLS
urlpatterns += [
    path('login-ajax/', login_ajax, name='login_ajax'),
    path('create-account/', create_account, name='create_account'),
    path('update-profile/', update_profile, name='update_profile'),
    path('delete-account/', delete_account, name='delete_account'),
    path('reset-password/', reset_password, name='reset_password'),
    path('create-patient/', create_patient, name='create_patient'),
    path('get-available-providers/', get_available_providers, name='get_available_providers'),
    path('link-provider/', link_provider, name='link_provider'),
    path('unlink-provider/', unlink_provider, name='unlink_provider'),
    path('update-patient/', update_patient, name='update_patient'),
    path('delete-patient/', delete_patient, name='delete_patient'),
]

# PATIENT URLS
urlpatterns += [
    path("api/patient/login/", patient_login, name="api_login"),
    path("api/patient/details", get_patient_details),
    path("api/patient/alert/yes", patient_alert_yes),
    path("api/patient/alert/no", patient_alert_no),
]

# DOCTOR URLS
urlpatterns += [
    path('api/doctor/login/', doctor_login_view),
    path('api/doctor/data/', get_doctor_data_view),
]