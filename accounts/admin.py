from django.contrib import admin

from accounts.models import User, UserBank

# Register your models here.
admin.site.register(User)
admin.site.register(UserBank)
