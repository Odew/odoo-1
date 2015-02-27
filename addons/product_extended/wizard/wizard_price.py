# -*- coding: utf-8 -*-

from openerp.exceptions import UserError
from openerp import api, models, fields, _

class WizardPrice(models.Model):
    _name = "wizard.price"
    _description = "Compute price wizard"

    info_field = fields.Text("Info", readonly=True)
    real_time_accounting = fields.Boolean("Generate accounting entries when real-time")
    recursive = fields.Boolean("Change prices of child BoMs too")

    @api.model
    def default_get(self, fields):
        res = super(WizardPrice, self).default_get(fields)
        rec_id = self.env.context.get('active_id')
        assert rec_id, _('Active ID is not set in Context.')
        Product = self.env['product.template'].browse(rec_id)
        res['info_field'] = str(Product.compute_price([], [Product.id], test=True))
        return res

    @api.one
    def compute_from_bom(self):
        model = self.env.context.get('active_model')
        if model != 'product.template':
            raise UserError(_('This wizard is build for product templates, while you are currently running it from a product variant.'))
        rec_id = self.env.context.get('active_id')
        assert rec_id, _('Active ID is not set in Context.')
        Product = self.env['product.template']
        prod = Product.browse(rec_id)
        Product.compute_price([], template_ids=[prod.id], real_time_accounting=self.real_time_accounting, recursive=self.recursive, test=False)
