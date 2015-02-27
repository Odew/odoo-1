# -*- coding: utf-8 -*-

from openerp import api, models, fields


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'


    @api.multi
    def compute_price(self, product_ids, template_ids=False, recursive=False, test=False, real_time_accounting = False):
        '''
        Will return test dict when the test = False
        Multiple ids at once?
        testdict is used to inform the user about the changes to be made
        '''
        testdict = {}
        if product_ids:
            ids = product_ids
            model = 'product.product'
        else:
            ids = template_ids
            model = 'product.template'
        for prod_id in ids:
            MrpBom = self.env['mrp.bom']
            if model == 'product.product':
                bom_id = MrpBom._bom_find(product_id=prod_id)
            else:
                bom_id = MrpBom._bom_find(product_tmpl_id=prod_id)
            if bom_id:
                # In recursive mode, it will first compute the prices of child boms
                bom = MrpBom.browse(bom_id)
                if recursive:
                    #Call compute_price on these subproducts
                    prod_list = bom.bom_line_ids.mapped('product_id.id')
                    res = self.compute_price(prod_list, recursive=recursive, test=test, real_time_accounting = real_time_accounting)
                    if test: 
                        testdict.update(res)
                #Use calc price to calculate and put the price on the product of the BoM if necessary
                price = self._calc_price(bom, test=test, real_time_accounting = real_time_accounting)
                if test:
                    testdict[prod_id] = price
        if test:
            return testdict
        else:
            return True


    @api.multi
    def _calc_price(self, bom, test = False, real_time_accounting=False):
        price = 0
        ProductUom = self.env['product.uom']
        for sbom in bom.bom_line_ids:
            my_qty = sbom.product_qty
            if not sbom.attribute_value_ids:
                # No attribute_value_ids means the bom line is not variant specific
                price += ProductUom._compute_price(sbom.product_id.uom_id.id, sbom.product_id.standard_price, sbom.product_uom.id) * my_qty

        if bom.routing_id:
            for wline in bom.routing_id.workcenter_lines:
                wc = wline.workcenter_id
                cycle = wline.cycle_nbr
                hour = (wc.time_start + wc.time_stop + cycle * wc.time_cycle) *  (wc.time_efficiency or 1.0)
                price += wc.costs_cycle * cycle + wc.costs_hour * hour
                price = ProductUom._compute_price(bom.product_uom.id, price, bom.product_id.uom_id.id)
        
        #Convert on product UoM quantities
        if price > 0:
            price = ProductUom._compute_price(bom.product_uom.id, price / bom.product_qty, bom.product_id.uom_id.id)

        product = self.browse(bom.product_tmpl_id.id)
        if not test:
            if (product.valuation != "real_time" or not real_time_accounting):
                product.write({'standard_price' : price})
            else:
                #Call wizard function here
                PriceWizard = self.env["stock.change.standard.price"].create({'new_price': price})
                PriceWizard.change_price()
        return price


class ProductBom(models.Model):
    _inherit = 'mrp.bom'
            
    standard_price = fields.Float(related='product_tmpl_id.standard_price', string="Standard Price")

