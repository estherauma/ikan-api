from common.utils import generate_uuid
import json
from contracts.models import ContractClause
from prismic.utils import PrismicUtils
from vessels.models import Vessel


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


def get_clause_order(clause_kind):
    return clause_order[clause_kind] if clause_kind in clause_order else None


def generate_static_contract_clauses(request, contract):
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
            content=json.dumps(clause_data),
            created_by=request.user.id,
            updated_by=request.user.id,
        )
        clause.save()


def get_clauses_to_be_added(request, contract):
    prismic_utils = PrismicUtils(request)
    clauses = contract.contract_clause.all()
    clauses_to_be_added = []

    existing_clause_kinds = {clause.kind for clause in clauses}
    required_clause_kinds = clause_order.keys()
    missing_clause_kinds = set(required_clause_kinds) - existing_clause_kinds
    missing_clause_kinds = sorted(missing_clause_kinds, key=lambda x: get_clause_order(x))
    for kind in missing_clause_kinds:
        form_questions = prismic_utils.get_form_questions(kind)
        for question in form_questions:
            if kind == 'contract-clauses-parties-requirement-fishers' and question['key'] == 'vessel':
                vessels = Vessel.objects.filter(created_by=request.user.id).values('app_ref', 'name')
                question['options'] = [{'value': v['app_ref'], 'label': v['name']} for v in vessels]
            # elif kind == 'contract-clauses-contract-validity':
            #     if question['key'] == 'validityStartDate' and contract.start_date:
            #         question['value'] = contract.start_date.strftime('%d/%m/%Y')
            #     elif question['key'] == 'validityEndDate' and contract.end_date:
            #         question['value'] = contract.end_date.strftime('%d/%m/%Y')
            #         question['placeholder'] = 'dd/mm/yyyy'

        # get clause form
        Form = prismic_utils.create_form(form_questions)
        form = Form()

        # TODO: translate name when language switching is implemented
        if kind == 'contract-clauses-parties-requirement-vessel':
            name = 'Parties to this contract - Party A'
        elif kind == 'contract-clauses-parties-requirement-fishers':
            name = 'Parties to this contract - Party B'
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
