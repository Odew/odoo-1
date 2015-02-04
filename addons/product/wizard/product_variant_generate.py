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
        product_variant = self.pool.get('product.template')
        res['product_id'] = context.active_id 
        # res['attribute_line_ids'] =   
        return res


    def write_attribute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        product_template_obj = self.pool.get('product.template')
        for wizard in self.browse(cr, uid, ids, context=context):
            for line in wizard.attribute_line_ids:
                product_template_obj.write(cr, uid, [wizard.product_id], {'attribute_line_ids': [(2, id,  attribute_line_ids)]})
                                

<field name="attribute_id"/>
                            <field name="value_ids"

        return product_template_obj.write(cr, uid, [product_id], {'attribute_line_ids': [(3, account_type_id)]})
