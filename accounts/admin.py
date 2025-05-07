from django.contrib import admin
from accounts.models import User, UserBank, UserBeneficiaries
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
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff')
    fieldsets = (
        (None, {
            'fields': (
                'id', 'email', 'password', 'last_login', 'first_name', 'last_name',
                'profile_image', 'telephone', 'mobile',
                'address_line_1', 'address_line_2', 'address_line_3',
                'city', 'country', 'postal_code', 'position',
                'is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
                'access_code', 'reset_password_token', 'registration_number', 'passport_number',
                'created_by', 'updated_by', 'deleted_by', 'deleted', 'deleted_at'
            )
        }),
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
