from django.contrib import admin
from .models import *

admin.site.register(UserProfiles)
admin.site.register(Patient)
admin.site.register(PatientLink)

class PatientLinkInline(admin.TabularInline):
    model = PatientLink
    extra = 1

class PatientAdmin(admin.ModelAdmin):
    inlines = [PatientLinkInline]

class UserProfilesAdmin(admin.ModelAdmin):
    inlines = [PatientLinkInline]

admin.site.unregister(Patient)
admin.site.unregister(UserProfiles)
admin.site.register(Patient, PatientAdmin)
admin.site.register(UserProfiles, UserProfilesAdmin)