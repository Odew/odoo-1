# -*- coding: utf-8 -*-

from openerp import models, api, _
from openerp.exceptions import Warning

class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model
    def _get_drop_shipping_route(self):
        try:
            ds_route_id = self.env.ref("stock_dropshipping.route_drop_shipping")
        except:
            ds_route_id = self.env['stock.location.route'].search([('name', 'like', _('Drop Shipping'))])
            ds_route_id = ds_route_id and ds_route_id[0] or False
        if not ds_route_id:
            raise Warning(_('Can\'t find any generic Drop Shipping route.'))
        return ds_route_id.id

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _check_routing(self, product, warehouse):
        res = super(sale_order_line, self)._check_routing(product, warehouse)
        if not res:
            for product_route in product.route_ids:
                try:
                    if product_route.id == self.env['stock.warehouse']._get_drop_shipping_route():
                        res = True
                        break
                except:
                    res = False
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
