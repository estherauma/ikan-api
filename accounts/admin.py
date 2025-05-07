from django.contrib import admin
from accounts.models import User, UserBank, UserBeneficiaries
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    USERNAME_FIELD = 'email'

    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff')
    # list_filter = ('is_staff',)
    fieldsets = (
        (None, {'fields': ('id', 'email', 'password', 'last_login', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name',  'first_name', 'last_name',)
    ordering = ('email',)


# Register your models here.
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserBank)
admin.site.register(UserBeneficiaries)
