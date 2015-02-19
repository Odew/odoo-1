# -*- coding: utf-8 -*-

from datetime import date

from openerp import api, fields, models


class Product(models.Model):
    _inherit = "product.product"

    @api.one
    def _product_margin(self):
        date_from = self.env.context.get('from_date', fields.Date.to_string(date(date.today().year, 1, 1)))
        date_to = self.env.context.get('to_date', fields.Date.to_string(date(date.today().year, 12, 31)))
        invoice_state = self.env.context.get('invoice_state', 'open_paid')
        self.date_from = date_from
        self.date_to = date_to
        self.invoice_state = invoice_state
        invoice_types = ()
        states = ()
        if invoice_state == 'paid':
            states = ('paid',)
        elif invoice_state == 'open_paid':
            states = ('open', 'paid')
        elif invoice_state == 'draft_open_paid':
            states = ('draft', 'open', 'paid')
        if "force_company" in self.env.context:
            company_id = self.env.context['force_company']
        else:
            company_id = self.env.user.company_id.id

        #Cost price is calculated afterwards as it is a property
        sqlstr = """select
                sum(l.price_unit * l.quantity)/sum(nullif(l.quantity * pu.factor / pu2.factor,0)) as avg_unit_price,
                sum(l.quantity * pu.factor / pu2.factor) as num_qty,
                sum(l.quantity * (l.price_subtotal/(nullif(l.quantity,0)))) as total,
                sum(l.quantity * pu.factor * pt.list_price / pu2.factor) as sale_expected
            from account_invoice_line l
            left join account_invoice i on (l.invoice_id = i.id)
            left join product_product product on (product.id=l.product_id)
            left join product_template pt on (pt.id = l.product_id)
                left join product_uom pu on (pt.uom_id = pu.id)
                left join product_uom pu2 on (l.uos_id = pu2.id)
            where l.product_id = %s and i.state in %s and i.type IN %s and (i.date_invoice IS NULL or (i.date_invoice>=%s and i.date_invoice<=%s and i.company_id=%s))
            """
        invoice_types = ('out_invoice', 'in_refund')
        self.env.cr.execute(sqlstr, (self.id, states, invoice_types, date_from, date_to, company_id))
        result = self.env.cr.fetchall()[0]
        self.sale_avg_price = result[0] and result[0] or 0.0
        self.sale_num_invoiced = result[1] and result[1] or 0.0
        self.turnover = result[2] and result[2] or 0.0
        self.sale_expected = result[3] and result[3] or 0.0
        self.sales_gap = self.sale_expected - self.turnover
        Product = self.env['product.product']
        product = Product.with_context(force_company=company_id).browse(self.id)
        invoice_types = ('in_invoice', 'out_refund')
        self.env.cr.execute(sqlstr, (self.id, states, invoice_types, date_from, date_to, company_id))
        result = self.env.cr.fetchall()[0]
        self.purchase_avg_price = result[0] and result[0] or 0.0
        self.purchase_num_invoiced = result[1] and result[1] or 0.0
        self.total_cost = result[2] and result[2] or 0.0
        self.normal_cost = product.standard_price * self.purchase_num_invoiced
        self.purchase_gap = self.normal_cost - self.total_cost

        self.total_margin = self.turnover - self.total_cost
        self.expected_margin = self.sale_expected - self.normal_cost
        self.total_margin_rate = self.turnover and self.total_margin * 100 / self.turnover or 0.0
        self.expected_margin_rate = self.sale_expected and self.expected_margin * 100 / self.sale_expected or 0.0

    date_from = fields.Date(compute='_product_margin', string='Margin Date From')
    date_to = fields.Date(compute='_product_margin', string='Margin Date To')
    invoice_state = fields.Selection(compute='_product_margin', selection=[('paid', 'Paid'), ('open_paid', 'Open and Paid'),
                                    ('draft_open_paid', 'Draft, Open and Paid')], readonly=True)
    sale_avg_price = fields.Float(compute='_product_margin', string='Avg. Unit Price', help="Avg. Price in Customer Invoices.")
    purchase_avg_price = fields.Float(compute='_product_margin', string='Avg. Unit Price', help="Avg. Price in Supplier Invoices ")
    sale_num_invoiced = fields.Float(compute='_product_margin', string='# Invoiced in Sale', help="Sum of Quantity in Customer Invoices")
    purchase_num_invoiced = fields.Float(compute='_product_margin', string='# Invoiced in Purchase', multi='product_margin', help="Sum of Quantity in Supplier Invoices")
    sales_gap = fields.Float(compute='_product_margin', help="Expected Sale - Turn Over")
    purchase_gap = fields.Float(compute='_product_margin', help="Normal Cost - Total Cost")
    turnover = fields.Float(compute='_product_margin', help="Sum of Multiplication of Invoice price and quantity of Customer Invoices")
    total_cost = fields.Float(compute='_product_margin', help="Sum of Multiplication of Invoice price and quantity of Supplier Invoices ")
    sale_expected = fields.Float(compute='_product_margin', string='Expected Sale', help="Sum of Multiplication of Sale Catalog price and quantity of Customer Invoices")
    normal_cost = fields.Float(compute='_product_margin', help="Sum of Multiplication of Cost price and quantity of Supplier Invoices")
    total_margin = fields.Float(compute='_product_margin', help="Turnover - Standard price")
    expected_margin = fields.Float(compute='_product_margin', help="Expected Sale - Normal Cost")
    total_margin_rate = fields.Float(compute='_product_margin', string='Total Margin Rate(%)', help="Total margin * 100 / Turnover")
    expected_margin_rate = fields.Float(compute='_product_margin', string='Expected Margin (%)', help="Expected margin * 100 / Expected Sale")
