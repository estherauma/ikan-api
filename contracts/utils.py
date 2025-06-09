from common.utils import generate_uuid
import json
from contracts.models import ContractClause
from prismic.utils import PrismicUtils


def generate_static_contract_clauses(request, contract):
    prismic_utils = PrismicUtils(request)
    prismic_utils.get_content()
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
