from django.db import models
from common.models import BaseModel, AuditableModel

class Contract(AuditableModel):
    name = models.CharField(max_length=255, null=False, blank=False)
    app_ref = models.CharField(max_length=255, null=False, blank=False)
    internal_ref = models.CharField(max_length=255, null=False, blank=False)
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    # TODO: Add foreigh keys when the company model is created 
    # taiwanese_company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='taiwanese_company')
    # indonesian_company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='indonesia_company')
    taiwanese_company = models.CharField(null=True, blank=True, max_length=255)
    indonesian_company = models.CharField(null=True, blank=True, max_length=255)
    kind = models.CharField(max_length=255, null=False, blank=False)
    

class ContractDocument(AuditableModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_document')
    name = models.CharField(max_length=255, null=False, blank=False)
    url = models.CharField(max_length=255, null=False, blank=False)
    status = models.CharField(max_length=255, null=False, blank=False)


class ContractClause(AuditableModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_clause')
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    order = models.IntegerField(null=False, blank=False)
    status = models.CharField(max_length=255, null=False, blank=False)