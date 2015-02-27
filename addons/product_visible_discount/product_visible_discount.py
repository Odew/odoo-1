# -*- coding: utf-8 -*-

from openerp import api, fields, models, _

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    visible_discount = fields.Boolean('Visible Discount', default=True)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False):

        def get_real_price(res_dict, product_id, qty, uom, pricelist):
            """Retrieve the price before applying the pricelist"""
            PriceItem = self.env['product.pricelist.item']
            PriceType = self.env['product.price.type']
            Product = self.env['product.product']
            field_name = 'list_price'
            rule_id = res_dict.get(pricelist) and res_dict[pricelist][1] or False
            if rule_id:
                item_base = PriceItem.browse(rule_id).base
                if item_base > 0:
                    field_name = PriceType.browse(item_base).field

            product = Product.browse(product_id)
            product_read = product.read([field_name])[0]

            factor = 1.0
            if uom and uom != product.uom_id.id:
                # the unit price is in a different uom
                factor = self.pool['product.uom']._compute_qty(uom, 1.0, product.uom_id.id)
            return product_read[field_name] * factor


        res=super(SaleOrderLine, self).product_id_change(pricelist, product, qty,
            uom, qty_uos, uos, name, partner_id,
            lang, update_tax, date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag)

        context = {'lang': lang, 'partner_id': partner_id}
        result=res['value']
        if product and pricelist and self.env['res.users'].has_group('sale.group_discount_per_so_line'):
            if result.get('price_unit',False):
                price=result['price_unit']
            else:
                return res
            uom = result.get('product_uom', uom)
            product = self.env['product.product'].browse(product)
            product_price = self.env['product.pricelist'].browse(pricelist)
            list_price = product_price.price_rule_get(
                    product.id, qty or 1.0, partner_id)

            new_list_price = get_real_price(list_price, product.id, qty, uom, pricelist)
            if product_price.visible_discount and list_price[pricelist][0] != 0 and new_list_price != 0:
                if product.company_id and product_price.currency_id.id != product.company_id.currency_id.id:
                    # new_list_price is in company's currency while price in pricelist currency
                    new_list_price = self.env['res.currency'].compute(
                        product.company_id.currency_id.id, product_price.currency_id.id,
                        new_list_price)
                discount = (new_list_price - price) / new_list_price * 100
                if discount > 0:
                    result['price_unit'] = new_list_price
                    result['discount'] = discount
                else:
                    result['discount'] = 0.0
            else:
                result['discount'] = 0.0
        else:
            result['discount'] = 0.0
        return res
