from django.contrib import admin

from accounts.models import User, UserBank, UserBeneficiaries

# Register your models here.
admin.site.register(User)
admin.site.register(UserBank)
admin.site.register(UserBeneficiaries)
