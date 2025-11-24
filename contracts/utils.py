from common.utils import generate_uuid
import json
from contracts.models import ContractClause
from prismic.utils import PrismicUtils
from vessels.models import Vessel
from common.utils import format_local_date
from common.utils import get_gcs_signed_url


clause_order = {
    'contract-clauses-parties-requirement-vessel': 0,
    'contract-clauses-parties-requirement-fishers': 0.1,
    'contract-clauses-contract-validity': 1,
    'contract-clauses-wage-benefits': 2,
    'contract-clauses-accident-medical-and-life-insurance': 3,
    'contract-clauses-transportation-severance-food-accomodation': 4,
    'contract-clauses-working-hours-rest-and-leave': 5,
    'contract-clauses-labor-protection-and-benefits': 6,
    'contract-clause-requirements-that-party-b-must-comply-with': 7,
    'contract-clauses-means-to-address-breach-of-contract': 8,
    'contract-clauses-dispute-settlement': 9,
    'contract-clauses-miscellaneous': 10,
    'contract-clauses-attachments': 11,
}


static_clauses = [
    'contract-clauses-accident-medical-and-life-insurance',
    'contract-clauses-transportation-severance-food-accomodation',
    'contract-clause-requirements-that-party-b-must-comply-with',
    'contract-clauses-means-to-address-breach-of-contract',
    'contract-clauses-dispute-settlement',
    'contract-clauses-miscellaneous',
]


dynamic_clauses = [
    'contract-clauses-parties-requirement-vessel',
    'contract-clauses-parties-requirement-fishers',
    'contract-clauses-contract-validity',
    'contract-clauses-wage-benefits',
    'contract-clauses-working-hours-rest-and-leave',
    'contract-clauses-labor-protection-and-benefits',
    'contract-clauses-attachments',
]


def get_clause_order(clause_kind):
    return clause_order[clause_kind] if clause_kind in clause_order else None


def generate_static_contract_clauses(request, contract, vessel_owner=None):
    prismic_utils = PrismicUtils(request)
    clause_mapping = {
        'article_3': 'contract-clauses-accident-medical-and-life-insurance',
        'article_4': 'contract-clauses-transportation-severance-food-accomodation',
        'article_7': 'contract-clause-requirements-that-party-b-must-comply-with',
        'article_8': 'contract-clauses-means-to-address-breach-of-contract',
        'article_9': 'contract-clauses-dispute-settlement',
        'article_10': 'contract-clauses-miscellaneous'
    }

    for key, value in clause_mapping.items():
        property_name = f'{value}-content'
        clause_data = prismic_utils.get_content_by_property_name(property_name)
        page_title = clause_data['pageTitle'] if clause_data else None

        clause = ContractClause.objects.create(
            app_ref=generate_uuid(),
            contract=contract,
            name=page_title,
            kind=value,
            content=json.dumps({}),
            created_by=vessel_owner if vessel_owner else request.user.id,
            updated_by=vessel_owner if vessel_owner else request.user.id,
        )
        clause.save()


def get_clause_form_questions(request, clause_kind, created_by=None):
    prismic_utils = PrismicUtils(request)
    form_questions = prismic_utils.get_form_questions(clause_kind)
    if not form_questions:
        return None

    for question in form_questions:
        if clause_kind == 'contract-clauses-parties-requirement-fishers' and question['key'] == 'vessel':
            generated_by = created_by if created_by else request.user.id
            vessels = Vessel.objects.filter(created_by=generated_by).values('app_ref', 'name')
            question['options'] = [{'value': v['app_ref'], 'label': v['name']} for v in vessels]
        # elif clause_kind == 'contract-clauses-contract-validity':
        #     if question['key'] == 'validityStartDate' and contract.start_date:
        #         question['value'] = contract.start_date.strftime('%d/%m/%Y')
        #     elif question['key'] == 'validityEndDate' and contract.end_date:
        #         question['value'] = contract.end_date.strftime('%d/%m/%Y')
        #         question['placeholder'] = 'dd/mm/yyyy'

    return form_questions


def get_clause_form(request, clause_kind, initial_data=None, created_by=None):
    prismic_utils = PrismicUtils(request)
    form_questions = get_clause_form_questions(request, clause_kind, created_by=created_by)
    if not form_questions:
        return None

    # get clause form
    Form = prismic_utils.create_form(form_questions)
    form = Form(initial=initial_data or {})
    return form


def get_clauses_to_be_added(request, contract):
    prismic_utils = PrismicUtils(request)
    common_text = prismic_utils.common_text
    clauses = contract.contract_clause.all()
    clauses_to_be_added = []

    existing_clause_kinds = {clause.kind for clause in clauses}
    required_clause_kinds = clause_order.keys()
    missing_clause_kinds = set(required_clause_kinds) - existing_clause_kinds
    missing_clause_kinds = sorted(missing_clause_kinds, key=lambda x: get_clause_order(x))
    for kind in missing_clause_kinds:
        created_by = contract.created_by if contract.created_by else request.user.id
        form_questions = get_clause_form_questions(request=request, clause_kind=kind, created_by=created_by)
        # get clause form
        form = get_clause_form(request=request, clause_kind=kind, created_by=created_by)

        # TODO: translate name when language switching is implemented
        if kind == 'contract-clauses-parties-requirement-vessel':
            name = common_text.get('partiesToThisContractPartyA', 'Parties to this contract - Party A---------')
        elif kind == 'contract-clauses-parties-requirement-fishers':
            name = common_text.get('partiesToThisContractPartyB', 'Parties to this contract - Party B----------')
        else:
            clause_data = prismic_utils.get_content_by_property_name(f'{kind}-content')
            name = clause_data['pageTitle'] if clause_data else kind.replace('-', ' ')

        clause_details = {
            'kind': kind,
            'name': name,
            'form': form,
            'form_questions': form_questions,
        }

        clauses_to_be_added.append(clause_details)
    return clauses_to_be_added


def get_clause_html_content(request, clause):
    prismic_utils = PrismicUtils(request)
    property_name = f'{clause.kind}-content'
    if clause.kind == 'contract-clauses-parties-requirement-vessel':
        property_name = 'contract-clauses-parties-to-this-contract-content'
    page_data = prismic_utils.get_content_by_property_name(property_name)
    page_content = page_data['pageContent'] if page_data and page_data['pageContent'] else None
    page_text_array = page_content[0]['description'] if page_content and page_content[0]['description'] else []
    text_html = ''

    for index, item in enumerate(page_text_array):
        #  add spacing between items
        if item['paragraph'].startswith('{{') and item['paragraph'].endswith('}}'):
            text_html += '<br/>'
            text_html += item['paragraph']
        else:
            text_html += '<br/><br/>'
            text_html += item['paragraph']

    # replace placeholders with values
    form_values = order_clause_data(request, clause.kind, clause.content)
    html_content = fill_placeholders(text_html, form_values)

    return html_content


def order_clause_data(request, clause_type, data):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return data
    if clause_type == 'contract-clauses-parties-requirement-vessel':
        return order_clause_one_data(request, clause_type, data)
    else:
        return order_other_clauses(request, clause_type, data)


def order_clause_one_data(request, clause_type, data):
    result = {}
    # TODO: remove after all old records are synced
    # This is a fix for old records that have different keys for rep details
    data = {
        **data,
        'representative': data.get('representative', data.get('respresentative', None)),
        'repAddress': data.get('repAddress', data.get('address', None)),
        'repTelephone': data.get('repTelephone', data.get('tel', None)),
    }
    # End of fix

    for key, value in data.items():
        formatted_value = format_clause_values(request, clause_type, key, value)
        result[key] = formatted_value

    # clause one has two entries, so we need to add the second entry from partyB details
    if 'party_b_clause_id' in data and data['party_b_clause_id']:
        party_b_clause_details = ContractClause.objects.filter(id=data['party_b_clause_id']).first()
        if party_b_clause_details:
            party_b_content = json.loads(party_b_clause_details.content) if party_b_clause_details.content else {}

            # TODO: remove after all old records are synced/updated
            # This is a fix for old records that have different keys for crew details
            party_b_content = {
                **party_b_content,
                'crewAddress': party_b_content.get('crewAddress', party_b_content.get('address', None)),
                'crewTelephone': party_b_content.get('crewTelephone', party_b_content.get('telephone', None)),
            }
            # End of fix

            for key, value in party_b_content.items():
                formatted_value = format_clause_values(request, clause_type, key, value)
                result[key] = formatted_value

            vessel_app_ref = party_b_content.get('vessel')
            if vessel_app_ref:
                vessel = Vessel.objects.filter(app_ref=vessel_app_ref).values('name', 'reg_no').first()
                if vessel:
                    result['vesselName'] = vessel['name']
                    result['vesselRegNo'] = vessel['reg_no']
    return result


def order_other_clauses(request, clause_type, data):
    if 'paymentFrequencyDetails' not in data:
        data.pop('paymentFrequencyDetails', None)

    result = {}
    for key, value in data.items():
        formatted_value = format_clause_values(request, clause_type, key, value)
        result[key] = formatted_value
    return result


def format_clause_values(request, clause_type, key, value):
    prismic_utils = PrismicUtils(request)
    if not value or not key:
        return value

    if 'date' in key.lower() and key not in ['updated_at', 'updated_by']:
        selected_language = request.session.get('language', 'en-us')
        return format_local_date(value, selected_language)
    elif key in ['partyASignature', 'partyBSignature']:
        signed_url = get_gcs_signed_url(value)
        if value.endswith('.pdf'):
            # return f'<embed src="{signed_url}" type="application/pdf" width="100%" height="500px"></embed>'
            return f'<a href="{signed_url}" target="_blank">View PDF Signature</a>'
        return f'<img class="image" src="{signed_url}" alt="image" style="max-width: 200px; max-height: 150px;"/>'
    elif clause_type == 'contract-clauses-parties-to-this-contract-content' and key == 'vessel':
        vessel = Vessel.objects.filter(app_ref=value).values('name').first()
        return vessel['name'] if vessel else None
    elif clause_type == 'contract-clauses-parties-to-this-contract-content' and key == 'crewMemberRole':
        return prismic_utils.get_question_option_translation('contract-clauses-parties-requirement-fishers', key, value)
    elif clause_type == 'contract-clauses-wage-benefits-content' and key in ['paymentFrequency', 'paymentMethod']:
        return prismic_utils.get_question_option_translation('contract-clauses-wage-benefits', key, value)
    elif clause_type == 'contract-clauses-attachments-content' and key == 'isCrewMemberAccount':
        return prismic_utils.get_question_option_translation('contract-clauses-attachments', key, value)

    return value


def fill_placeholders(input_string, placeholder_values):
    result = input_string
    for key, value in placeholder_values.items():
        placeholder = f'{{{{{key}}}}}'
        if not isinstance(value, str):
            value = str(value)
        result = result.replace(placeholder, value)
    return result


def get_add_contract_form_labels(request):
    prismic_utils = PrismicUtils(request)
    labels = prismic_utils.get_field_labels_from_form_questions(None, 'companies-createcontract')

    labels['kind'] = labels.get('type', 'Kind')
    labels['taiwanese_company'] = labels.get('taiwanese_company_id', 'Taiwanese Company Name')
    labels['indonesian_company'] = labels.get('indonesian_company_id', 'Indonesian Company Name')
    labels['upload_contract'] = labels.get('file', 'Upload contract')
    labels['select_option'] = prismic_utils.common_text.get('selectOption', 'Select option')
    labels['company'] = prismic_utils.common_text.get('company', 'Company')
    labels['worker'] = prismic_utils.common_text.get('worker', 'Worker')

    return labels
