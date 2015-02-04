# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields, osv


class product_variant_generate(osv.osv_memory):
    _name = 'product.variant_generate'
    _description = 'Product Variant Generate'

    _columns = {
        'attribute_line_ids': fields.one2many('product.attribute.line', 'product_tmpl_id', 'Product Attributes'),
        'product_id': fields.many2one('product.template'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = {}
        res['product_id'] = context['active_id'] 
        return res


    def write_attribute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        product_template_obj = self.pool.get('product.template')
        product_attribute_line_obj = self.pool.get('product.attribute.line')

        for wizard in self.browse(cr, uid, ids, context=context):
            lines = []
            actual_product_attribute = [att.id for att in wizard.product_id.attribute_line_ids]
            for wiz_line in wizard.attribute_line_ids:
                if wiz_line.attribute_id.id not in actual_product_attribute:
                    # need to add 
                    value_ids = [(4, v.id) for v in wiz_line.value_ids]
                    attribute_line_value = {
                        'product_tmpl_id': wizard.product_id.id,
                        'attribute_id': wiz_line.attribute_id.id,
                        'value_ids': value_ids
                    }
                    lines.append((0, False , attribute_line_value))

            actual_wizard_attribute = [att.id for att in wizard.attribute_line_ids]
            for prod_line in wizard.product_id.attribute_line_ids:
                if prod_line.attribute_id.id not in actual_wizard_attribute:
                    # need to remove
                    product_attribute_line_obj.unlink(cr, uid, [prod_line.id], context=context)

            # final and only WRITE
            product_template_obj.write(cr, uid, [wizard.product_id.id], {'attribute_line_ids': lines})

                