# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015-TODAY OpenERP s.a. (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, models

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_line_move_line_get(self):
        res = super(account_invoice,self).invoice_line_move_line_get()

        if self.type in ('in_invoice', 'out_invoice'):
            return res

        _res = []
        for _line in res:
            if _line.get('product_id', False):
                _product_id = _line.product_id
                if _product_id.valuation == 'real_time':
                    acc_out = _product_id.property_stock_account_output 
                    if not acc_out:
                        acc_out = _product_id.categ_id.property_stock_account_output_categ 

                    acc_in = _product_id.property_stock_account_input
                    if not acc_in:
                        acc_in = _product_id.categ_id.property_stock_account_input_categ

                    if acc_out and acc_in:
                        if inv.type == 'in_refund' and _line['account_id'] == acc_out:
                            _line['account_id'] = acc_in
                    if inv.type == 'out_refund' and _line['account_id'] == acc_in:
                            _line['account_id'] = acc_out
            _res.append(_line)
        return _res
    
class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, company_id=None):
        res = super(account_invoice_line, self).product_id_change(product, uom_id, qty, name, type, partner_id, fposition_id, price_unit, currency_id, company_id)
        if not product:
            return res
        if type in ('in_invoice','in_refund'):
            oa = product.property_stock_account_input
            if not oa:
                oa = product.categ_id.property_stock_account_input_categ
            if oa:
                fpos = fposition_id or False
                a = fpos.map_account(oa)
                res['value'].update({'account_id': a})
        return res
