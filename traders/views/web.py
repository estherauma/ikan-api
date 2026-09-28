from accounts.forms import AttachTraderVesselOwnersForm, InviteUser, ResendTokenForm
from accounts.mixins import RoleRequiredMixin
from accounts.models import TraderVesselOwnerRelationship, User
from accounts.utils import send_user_invite_email
from common.services.translation import Translator
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from traders.services.payments import WagePaymentsService


class TraderDashboardOverviewView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = 'traders/dashboard/overview.html'
    required_roles = ['trader']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        translator = Translator(self.request)
        wage_payments_service = WagePaymentsService(
            self.request.user,
            translator,
        )

        context['overview_summary'] = wage_payments_service.get_overview_summary()
        return context


class TraderDashboardWagePaymentsView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = 'traders/dashboard/wage_payments.html'
    required_roles = ['trader']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        translator = Translator(self.request)
        wage_payments_service = WagePaymentsService(self.request.user, translator)
        context['payment_summary'] = wage_payments_service.get_payment_summary()
        context['supplier_filters'] = [
            translator.t('status'),
            # translator.t('date'),
        ]
        context['status_filter_options'] = [
            {
                'label': translator.t('all'),
                'value': 'all',
            },
            {
                'label': translator.t('noIssues'),
                'value': 'no_issues',
            },
            {
                'label': translator.t('nonCompliant'),
                'value': 'non_compliant',
            },
        ]
        context['supplier_rows'] = wage_payments_service.get_supplier_rows()
        return context


class TradersListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = User
    context_object_name = 'traders'
    template_name = 'traders/list.html'
    required_roles = ['admin']

    def get_queryset(self):
        return User.objects.filter(groups__name='trader').prefetch_related('groups')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invite_user_form'] = InviteUser()
        context['resend_token_form'] = ResendTokenForm()
        context['traders'] = self.get_queryset()
        context['show_invite_modal'] = False
        return context


class InviteTraderView(LoginRequiredMixin, RoleRequiredMixin, View):
    required_roles = ['admin']

    def post(self, request):
        form = InviteUser(request.POST)
        translator = Translator(request)
        invite_email_text = {
            **translator.content_utils.get_page_text('auth-common-text'),
            **translator.common_text,
        }

        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data(),
                'message': translator.t('errorOccurred'),
            }, status=400)

        user = User.objects.create_user(
            email=form.cleaned_data.get('email'),
            mobile=form.cleaned_data.get('mobile'),
            first_name=form.cleaned_data.get('first_name'),
            last_name=form.cleaned_data.get('last_name'),
            is_active=False,
            access_code=None,
            created_by=request.user,
            updated_by=request.user,
        )
        trader_group = Group.objects.get(name='trader')
        user.groups.add(trader_group)

        if form.cleaned_data.get('has_email'):
            success = send_user_invite_email(user, invite_email_text)
            if not success:
                return JsonResponse({
                    'success': False,
                    'message': translator.t('errorOccurred'),
                }, status=500)

        return JsonResponse({
            'success': True,
            'message': translator.t('userCreatedSuccessMsg'),
        })


class TraderDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = User
    template_name = 'traders/detail.html'
    context_object_name = 'trader'
    required_roles = ['admin']

    def get_queryset(self):
        return User.objects.filter(groups__name='trader').prefetch_related('groups')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vessel_owner_relationships'] = TraderVesselOwnerRelationship.objects.filter(
            trader=self.object,
        ).select_related('vessel_owner')
        attach_vessel_owners_form = kwargs.get(
            'attach_vessel_owners_form',
            AttachTraderVesselOwnersForm(trader=self.object),
        )
        selected_vessel_owner_ids = attach_vessel_owners_form.data.getlist('vessel_owners')
        available_vessel_owner_options = []
        for vessel_owner in attach_vessel_owners_form.fields['vessel_owners'].queryset:
            name = f'{vessel_owner.first_name} {vessel_owner.last_name}'.strip()
            contact = vessel_owner.email or vessel_owner.mobile
            label = name or contact
            available_vessel_owner_options.append({
                'value': vessel_owner.id,
                'label': label,
                'search_text': f'{name} {contact}',
                'selected': str(vessel_owner.id) in selected_vessel_owner_ids,
            })

        context['attach_vessel_owners_form'] = attach_vessel_owners_form
        context['available_vessel_owner_options'] = available_vessel_owner_options
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = AttachTraderVesselOwnersForm(data=request.POST, trader=self.object)

        if not form.is_valid():
            return JsonResponse({'success': False, 'errors': form.errors.get_json_data()}, status=400)

        relationships = [
            TraderVesselOwnerRelationship(
                trader=self.object,
                vessel_owner=vessel_owner,
                created_by=request.user,
                updated_by=request.user,
            )
            for vessel_owner in form.cleaned_data['vessel_owners']
        ]
        TraderVesselOwnerRelationship.objects.bulk_create(relationships)
        translator = Translator(request)
        messages.success(request, translator.t('VOattachSuccessMsg'))
        return JsonResponse({'success': True})


class RemoveTraderVesselOwnerRelationshipView(LoginRequiredMixin, RoleRequiredMixin, View):
    required_roles = ['admin']

    def post(self, request, pk, relationship_pk):
        trader = get_object_or_404(User.objects.filter(groups__name='trader'), pk=pk)
        relationship = get_object_or_404(
            TraderVesselOwnerRelationship,
            pk=relationship_pk,
            trader=trader,
        )
        relationship.delete()
        return JsonResponse({'success': True})


class ResendTraderInviteView(LoginRequiredMixin, RoleRequiredMixin, View):
    required_roles = ['admin']

    def post(self, request):
        form = ResendTokenForm(data=request.POST)
        translator = Translator(request)
        invite_email_text = {
            **translator.content_utils.get_page_text('auth-common-text'),
            **translator.common_text,
        }

        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data(),
                'message': translator.t('errorOccurred'),
            }, status=400)

        email = form.cleaned_data.get('email')
        user = User.objects.filter(email=email, groups__name='trader').first()
        if not user:
            return JsonResponse({
                'success': False,
                'message': translator.t('userDoesnotExist'),
            }, status=404)

        success = send_user_invite_email(user, invite_email_text)
        if success:
            return JsonResponse({
                'success': True,
                'message': translator.t('sentInviteSuccessMsg'),
            })
        return JsonResponse({
            'success': False,
            'message': translator.t('errorOccurred'),
        }, status=500)
