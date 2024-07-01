from django.contrib import admin
from survey.models import Survey, InlineQuestion

admin.site.register(Survey)
admin.site.register(InlineQuestion)
