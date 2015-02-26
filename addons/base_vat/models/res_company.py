# -*- coding: utf-8 -*-
from openerp import fields, models

class ResCompanyVat(models.Model):
    _inherit = 'res.company'

    vat_check_vies = fields.Boolean(
        string='VIES VAT Check', help="If checked, Partners VAT numbers will be fully validated against EU's VIES service "
        "rather than via a simple format validation (checksum).")
