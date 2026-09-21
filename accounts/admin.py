from django.contrib import admin
from accounts.admin_utils import set_created_by_choices
from accounts.models import AgentVesselOwnerRelationship, TraderVesselOwnerRelationship, User, UserBank, UserBeneficiaries
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')


class CustomUserChangeForm(UserChangeForm):
    created_by = forms.ChoiceField(required=False)

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_created_by_choices(self)


class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = (
        'email',
        'mobile',
        'first_name',
        'last_name',
        'created_at',
        'updated_at',
        'display_groups',
        'is_active',
        'is_staff'
    )
    list_display_links = [
        "email",
        "mobile",
    ]
    fieldsets = (
        (None, {
            'fields': (
                'id', 'email', 'password', 'last_login', 'first_name', 'last_name',
                'profile_image', 'telephone', 'is_telephone_verified', 'mobile', 'is_mobile_verified',
                'address_line_1', 'address_line_2', 'address_line_3',
                'city', 'country', 'postal_code', 'position',
                'is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
                'access_code', 'reset_password_token', 'registration_number', 'passport_number',
                'created_by', 'updated_by', 'recruited_by', 'deleted_by', 'deleted', 'deleted_at'
            )
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'mobile', 'first_name', 'last_name', 'groups__name')
    ordering = ('email', 'mobile',)

    def display_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    display_groups.short_description = "Groups"


# Register your models here.
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserBank)
admin.site.register(UserBeneficiaries)
admin.site.register(AgentVesselOwnerRelationship)
admin.site.register(TraderVesselOwnerRelationship)
