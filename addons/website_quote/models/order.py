# -*- coding: utf-8 -*-

import datetime
import uuid

from openerp import api, fields, models
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

import openerp.addons.decimal_precision as dp


class SaleQuoteTemplate(models.Model):
    _name = "sale.quote.template"
    _description = "Sale Quotation Template"

    name = fields.Char('Quotation Template', required=True)
    website_description = fields.Html(string='Description', translate=True)
    quote_line = fields.One2many('sale.quote.line', 'quote_id', string='Quotation Template Lines', copy=True)
    note = fields.Text(string='Terms and conditions')
    options = fields.One2many('sale.quote.option', 'template_id', string='Optional Products Lines', copy=True)
    number_of_days = fields.Integer(string='Quotation Duration', help='Number of days for the validity date computation of the quotation')

    @api.multi
    def action_open_template(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/quote/template/%d' % self.id
        }


class SaleQuoteLine(models.Model):
    _name = "sale.quote.line"
    _description = "Quotation Template Lines"

    sequence = fields.Integer(help="Gives the sequence order when displaying a list of sale quote lines.", default=10)
    quote_id = fields.Many2one('sale.quote.template', string='Quotation Template Reference', required=True, ondelete='cascade', index=True)
    name = fields.Text(string='Description', required=True, translate=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], required=True)
    website_description = fields.Html(string='Line Description', related="product_id.product_tmpl_id.quote_description", translate=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits_compute=dp.get_precision('Product Price'))
    discount = fields.Float(digits_compute=dp.get_precision('Discount'))
    product_uom_qty = fields.Float(string='Quantity', required=True, digits_compute=dp.get_precision('Product UoS'), default=1)
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure ', required=True)

    _order = 'sequence, id'

    @api.onchange('product_id')
    def on_change_product_id(self):
        product = self.product_id
        name = product.name
        if product.description_sale:
            name += '\n' + product.description_sale

        self.price_unit = product.list_price
        self.product_uom_id = product.uom_id.id
        self.website_description = product and (product.quote_description or product.website_description) or ''
        self.name = name

    def _inject_quote_description(self, values):
        values = dict(values or {})
        if not values.get('website_description') and values.get('product_id'):
            product = self.env['product.product'].browse(values['product_id'])
            values['website_description'] = product.quote_description or product.website_description or ''
        return values

    @api.model
    def create(self, values):
        values = self._inject_quote_description(values)
        quote_line = super(SaleQuoteLine, self).create(values)
        # hack because create don t make the job for a related field
        if values.get('website_description'):
            quote_line.write({'website_description': values['website_description']})
        return quote_line

    @api.multi
    def write(self, values):
        values = self._inject_quote_description(values)
        return super(SaleQuoteLine, self).write(values)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _description = "Sales Order Line"

    website_description = fields.Html(string='Line Description')
    option_line_id = fields.One2many('sale.order.option', 'line_id', string='Optional Products Lines')

    def _inject_quote_description(self, values):
        values = dict(values or {})
        if not values.get('website_description') and values.get('product_id'):
            product = self.env['product.product'].browse(values['product_id'])
            values['website_description'] = product.quote_description or product.website_description
        return values

    @api.model
    def create(self, values):
        values = self._inject_quote_description(values)
        order_line = super(SaleOrderLine, self).create(values)
        # hack because create don t make the job for a related field
        if values.get('website_description'):
            order_line.website_description = values['website_description']
        return order_line

    @api.multi
    def write(self, values):
        values = self._inject_quote_description(values)
        return super(SaleOrderLine, self).write(values)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    def _compute_amount_undiscounted(self):
        total = 0.0
        for line in self.order_line:
            total += (line.product_uom_qty * line.price_unit)
        self.amount_undiscounted = total

    def _default_template_id(self):
        try:
            quote_template = self.env.ref('website_quote.website_quote_template_default')
        except ValueError:
            quote_template = self.template_id
        return quote_template

    access_token = fields.Char(string='Security Token', required=True, copy=False, default=lambda self: str(uuid.uuid4()))
    template_id = fields.Many2one('sale.quote.template', string='Quotation Template', default=_default_template_id, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    website_description = fields.Html(string='Description')
    options = fields.One2many('sale.order.option', 'order_id', string='Optional Products Lines', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=True)
    amount_undiscounted = fields.Float(compute="_compute_amount_undiscounted", string='Amount Before Discount', digits_compute=dp.get_precision('Account'))
    quote_viewed = fields.Boolean(string='Quotation Viewed')

    @api.multi
    def action_open_quotation(self):
        self.ensure_one()
        self.quote_viewed = True
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/quote/%s' % (self.id)
        }

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            SaleOrderLine = self.env['sale.order.line']

            partner = self.partner_id
            context = dict(self.env.context)
            if partner:
                context.update({'lang': partner.lang})

            lines = [(5,)]
            quote_template = self.template_id.with_context(context)
            for line in quote_template.quote_line:
                result = SaleOrderLine.with_context(context).product_id_change(False, line.product_id.id, line.product_uom_qty, line.product_uom_id.id, line.product_uom_qty,
                    line.product_uom_id.id, line.name, partner.id, False, True, fields.Date.today(),
                    False, self.fiscal_position, True)
                data = result.get('value', {})
                if 'tax_id' in data:
                    data['tax_id'] = [(6, 0, data['tax_id'])]
                data.update({
                    'name': line.name,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'website_description': line.website_description,
                    'state': 'draft',
                })
                lines.append((0, 0, data))
            options = []
            for option in quote_template.options:
                options.append((0, 0, {
                    'product_id': option.product_id.id,
                    'name': option.name,
                    'quantity': option.quantity,
                    'uom_id': option.uom_id.id,
                    'price_unit': option.price_unit,
                    'discount': option.discount,
                    'website_description': option.website_description,
                }))
            date = False
            if quote_template.number_of_days > 0:
                date = (datetime.datetime.now() + datetime.timedelta(quote_template.number_of_days)).strftime(DF)

            self.order_line = lines
            self.website_description = quote_template.website_description
            self.note = quote_template
            self.options = options
            self.validity_date = date

    @api.multi
    def recommended_products(self):
        products = []
        for line in self.order_line:
            products += line.product_id.product_tmpl_id.recommended_products()
        return products

    @api.multi
    def get_access_action(self):
        self.ensure_one()
        """ Override method that generated the link to access the document. Instead
        of the classic form view, redirect to the online quote if exists. """
        if not self.template_id:
            return super(SaleOrder, self).get_access_action()
        return {
            'type': 'ir.actions.act_url',
            'url': '/quote/%s' % self.id,
            'target': 'self',
            'res_id': self.id,
        }

    @api.multi
    def action_quotation_send(self):
        self.ensure_one()
        action = super(SaleOrder, self).action_quotation_send()
        quote_template_id = self.browse(self.template_id)
        if quote_template_id.id:
            try:
                template_id = self.env.ref('website_quote.email_template_edi_sale').id
            except ValueError:
                pass
            else:
                action['context'].update({
                    'default_template_id': template_id,
                    'default_use_template': True
                })

        return action


class SaleQuoteOption(models.Model):
    _name = "sale.quote.option"
    _description = "Quotation Option"

    template_id = fields.Many2one('sale.quote.template', string='Quotation Template Reference', ondelete='cascade', index=True, required=True)
    name = fields.Text(string='Description', required=True, translate=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], required=True)
    website_description = fields.Html(string='Option Description', translate=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits_compute=dp.get_precision('Product Price'))
    discount = fields.Float(digits_compute=dp.get_precision('Discount'))
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    quantity = fields.Float(required=True, digits_compute=dp.get_precision('Product UoS'), default=1)

    @api.onchange('product_id')
    def on_change_product_id(self):
        product = self.product_id
        self.price_unit = product.list_price
        self.website_description = product.product_tmpl_id.quote_description
        self.name = product.name
        self.uom_id = product.product_tmpl_id.uom_id.id


class SaleOrderOption(models.Model):
    _name = "sale.order.option"
    _description = "Sale Options"

    order_id = fields.Many2one('sale.order', string='Sale Order Reference', ondelete='cascade', index=True)
    line_id = fields.Many2one('sale.order.line', string='Sale Order Line', on_delete="set null")
    name = fields.Text(string='Description', required=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)])
    website_description = fields.Html(string='Line Description')
    price_unit = fields.Float(string='Unit Price', required=True, digits_compute=dp.get_precision('Product Price'))
    discount = fields.Float(digits_compute=dp.get_precision('Discount'))
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    quantity = fields.Float(required=True, digits_compute=dp.get_precision('Product UoS'), default=1)

    @api.onchange('product_id')
    def on_change_product_id(self):
        if self.product_id:
            product = self.product_id

            self.price_unit = product.list_price
            self.website_description = product and (product.quote_description or product.website_description)
            self.name = product.name
            self.uom_id = product.product_tmpl_id.uom_id.id


class ProductTemplate(models.Model):
    _inherit = "product.template"

    website_description = fields.Html(string='Description for the website')  # hack, if website_sale is not installed
    quote_description = fields.Html(string='Description for the quote')
