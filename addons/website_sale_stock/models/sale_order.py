# -*- coding: utf-8 -*-

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class sale_order(osv.Model):
    _inherit = "sale.order"

    def _website_product_id_change(self, cr, uid, ids, order_id, product_id, qty=0, line_id=None, context=None):
        website_obj = self.pool['website']
        website_id = website_obj.search(cr, SUPERUSER_ID, [], limit=1)
        website = website_obj.browse(cr, SUPERUSER_ID, website_id, context=context)
        values = {}
        if website.warning_active:
            so = self.pool['sale.order'].browse(cr, uid, order_id, context=context)
            values = self.pool['sale.order.line'].product_id_change_with_wh(cr, SUPERUSER_ID, [],
                pricelist=so.pricelist_id.id,
                product=product_id,
                partner_id=so.partner_id.id,
                fiscal_position=so.fiscal_position.id,
                qty=qty,
                context=context
            )
        res = super(sale_order, self)._website_product_id_change(cr, uid, ids, order_id, product_id, qty, line_id, context)
        if values.get('warning'):
            product = self.pool['product.product'].browse(cr, SUPERUSER_ID, product_id, context)
            res['product_uom_qty'] = product.virtual_available
            if product.virtual_available <= 0:
                res['warning'] = _('Sorry ! The %s is out of stock.') % (product.name_get()[0][1])
            else:
                res['warning'] = _('Sorry ! Only %s units of %s are still in stock.') % (int  (product.virtual_available), product.name_get()[0][1])
        return res

class website(orm.Model):
    _inherit = 'website'

    def _get_options(self, cr, uid, ids, field_name, arg, context=None):
        customize_option = self.pool['ir.model.data'].xmlid_to_object(cr, SUPERUSER_ID, 'website_sale_stock.products_out_of_stock_warning')
        res = {id : customize_option.active for id in ids}
        return res

    _columns = {
        'warning_active': fields.function(_get_options, type="boolean", string='Out of Stock Warning')
    }
