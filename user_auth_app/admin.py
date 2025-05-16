from django.contrib import admin

from user_auth_app.models import Profile

class ProfilAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'fullname']


admin.site.register(Profile, ProfilAdmin)