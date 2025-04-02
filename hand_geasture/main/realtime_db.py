import time
import os
import firebase_admin
from firebase_admin import credentials, db
from django.contrib.auth.models import User
from .models import UserProfiles, PatientLink


cred_path = os.path.join(os.path.dirname(__file__), "/etc/secrets/hostpital-geasture-firebase-adminsdk.json")

if not os.path.exists(cred_path):
    raise FileNotFoundError(f"Firebase credentials file not found: {cred_path}")
else:
    print(f"Firebase credentials file found at: {cred_path}")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://hostpital-geasture-default-rtdb.asia-southeast1.firebasedatabase.app/'
})


def reset_and_insert_data():
    ref = db.reference('users')

    ref.delete()

    all_users = UserProfiles.objects.filter(role__in=['nurse', 'doctor'])
    main_data = {}

    for user in all_users:
        patients_data = {}
        patients = PatientLink.objects.filter(account=user)
        for patient in patients:
            patients_data[patient.patient.id] = {
                "age": patient.patient.age,
                "alert": patient.patient.alert,
                "name": patient.patient.name
            }
        user_data = {
            "username": user.user.username,
            "role": user.role,
            "patients": patients_data,
        }
        main_data[user.user.id] = user_data

    ref.set(main_data)

    return {"status": "Success", "message": "Database reset and new data inserted"}

