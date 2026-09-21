from accounts.forms import AttachTraderVesselOwnersForm, InviteUser, ResendTokenForm
from accounts.mixins import RoleRequiredMixin
from accounts.models import TraderVesselOwnerRelationship, User
from accounts.utils import send_user_invite_email
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from prismic.utils import PrismicUtils
from traders.services.payments import WagePaymentsService


class TraderDashboardOverviewView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = 'traders/dashboard/overview.html'
    required_roles = ['trader']


class TraderDashboardWagePaymentsView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = 'traders/dashboard/wage_payments.html'
    required_roles = ['trader']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wage_payments_service = WagePaymentsService(self.request.user)
        context['payment_summary'] = {
            'completion': wage_payments_service.get_payment_completion_summary(),
            'metric_groups': [
                {
                    'title': 'Deductions',
                    'items': [
                        {'label': 'Reported as none', 'percent': 77, 'color': '#65E878'},
                        {'label': 'No feedback', 'percent': 20, 'color': '#FF9824'},
                        {'label': 'Deduction reported', 'percent': 3, 'color': '#F44E5E'},
                    ],
                },
                {
                    'title': 'Payment timing',
                    'items': [
                        {'label': 'Received on-time', 'percent': 77, 'color': '#65E878'},
                        {'label': '1-30 days late', 'percent': 20, 'color': '#FF9824'},
                        {'label': '> 30 days late', 'percent': 3, 'color': '#F44E5E'},
                    ],
                },
                {
                    'title': 'Payslip status',
                    'items': [
                        {'label': 'Signed', 'percent': 77, 'color': '#65E878'},
                        {'label': 'Signature pending', 'percent': 20, 'color': '#FF9824'},
                        {'label': 'No payslip', 'percent': 3, 'color': '#F44E5E'},
                    ],
                },
            ],
        }
        context['supplier_filters'] = ['Tags', 'Date']
        context['supplier_rows'] = [
            {
                'name': 'Supplier / Vessel Owner 1',
                'summary': 'VESSEL A, VESSEL B, VESSEL C | 45 CREW',
                'status': 'No issues',
                'status_class': 'good',
                'is_expanded': False,
                'payslip_count': 30,
                'payslips': [
                    {
                        'worker_name': 'Budi Suharto',
                        'role': 'Engineer',
                        'amount': 'US$ 500.00',
                        'status': 'Submitted confirmation',
                        'status_class': 'submitted',
                    },
                    {
                        'worker_name': 'Budi Suharto',
                        'role': 'Deckhand',
                        'amount': 'US$ 400.00',
                        'status': 'Pending review/signature on payslip',
                        'status_class': 'pending',
                    },
                ],
            },
            {
                'name': 'Supplier / Vessel Owner 2',
                'summary': 'VESSEL D | 30 CREW',
                'status': 'Non-compliant',
                'status_class': 'danger',
                'is_expanded': True,
                'payslip_count': 30,
                'payslips': [
                    {
                        'worker_name': 'Budi Suharto',
                        'role': 'Engineer',
                        'amount': 'US$ 500.00',
                        'status': 'Submitted confirmation',
                        'status_class': 'submitted',
                    },
                    {
                        'worker_name': 'Budi Suharto',
                        'role': 'Deckhand',
                        'amount': 'US$ 400.00',
                        'status': 'Pending review/signature on payslip',
                        'status_class': 'pending',
                    },
                ],
            },
        ]
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
        prismic_utils = PrismicUtils(self.request)
        context['auth_common_text'] = prismic_utils.get_page_text('auth-common-text')
        context['common_text'] = prismic_utils.get_common_text()
        context['show_invite_modal'] = False
        return context


class InviteTraderView(LoginRequiredMixin, RoleRequiredMixin, View):
    required_roles = ['admin']

    def post(self, request):
        form = InviteUser(request.POST)
        auth_common_text = PrismicUtils(request).get_page_text('auth-common-text')
        common_text = PrismicUtils(request).get_common_text()

        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data(),
                'message': 'Error validating form!',
            }, status=400)

        user = User.objects.create_user(
            email=form.cleaned_data.get('email'),
            mobile=form.cleaned_data.get('mobile'),
            first_name=form.cleaned_data.get('first_name'),
            last_name=form.cleaned_data.get('last_name'),
            is_active=False,
            access_code=None,
            created_by=request.user.id,
            updated_by=request.user.id,
        )
        trader_group = Group.objects.get(name='trader')
        user.groups.add(trader_group)

        if form.cleaned_data.get('has_email'):
            success = send_user_invite_email(user, {**auth_common_text, **common_text})
            if not success:
                return JsonResponse({
                    'success': False,
                    'message': common_text.get(
                        'errorOccurred',
                        'User created but an error occurred while sending the email. Please contact support.'
                    ),
                }, status=500)

        return JsonResponse({
            'success': True,
            'message': common_text.get(
                'userCreatedSuccessMsg',
                'User created and email sent successfully.'
            ),
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
        prismic_utils = PrismicUtils(self.request)
        context['auth_common_text'] = prismic_utils.get_page_text('auth-common-text')
        context['common_text'] = prismic_utils.get_common_text()
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
                created_by=request.user.id,
                updated_by=request.user.id,
            )
            for vessel_owner in form.cleaned_data['vessel_owners']
        ]
        TraderVesselOwnerRelationship.objects.bulk_create(relationships)
        common_text = PrismicUtils(request).get_common_text()
        messages.success(request, common_text.get('VOattachSuccessMsg', 'Vessel owners attached successfully.'))
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
        common_text = PrismicUtils(request).get_common_text()
        auth_common_text = PrismicUtils(request).get_page_text('auth-common-text')
        
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data(),
                'message': common_text.get('errorOccurred', 'No valid email provided.'),
            }, status=400)

        email = form.cleaned_data.get('email')
        user = User.objects.filter(email=email, groups__name='trader').first()
        if not user:
            return JsonResponse({
                'success': False,
                'message': common_text.get('userDoesnotExist', 'User does not exist.'),
            }, status=404)

        success = send_user_invite_email(user, {**auth_common_text, **common_text})
        if success:
            return JsonResponse({
                'success': True,
                'message': common_text.get('sentInviteSuccessMsg', 'The invite was sent successfully.'),
            })
        return JsonResponse({
            'success': False,
            'message': common_text.get('errorOccurred', 'An error occurred while resetting the invite.'),
        }, status=500)
