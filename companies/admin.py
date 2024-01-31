from django.contrib import admin
from companies.models import Company, UserCompany

admin.site.register(Company)
admin.site.register(UserCompany)
