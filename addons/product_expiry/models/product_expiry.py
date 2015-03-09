# -*- coding: utf-8 -*-

import datetime
from openerp import api, fields, models


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    def _get_date(self, dtype):
        """Return computed limit date for a given date type."""
        product_id = self.env.context.get('product_id')
        if not product_id:
            date = False
        else:
            product = self.env['product.product'].browse(product_id)
            duration = getattr(product, dtype)
            # set date to False when no expiry time specified on the product
            date = duration and (datetime.datetime.today() + datetime.timedelta(days=duration))
        return date and fields.Datetime.to_string(date) or False

    life_date = fields.Datetime(string='End of Life Date', default=lambda self: self._get_date('life_time'),
        help='This is the date on which the goods with this Serial Number may become dangerous and must not be consumed.')
    use_date = fields.Datetime(string='Best before Date', default=lambda self: self._get_date('use_time'),
        help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.')
    removal_date = fields.Datetime(default=lambda self: self._get_date('removal_time'),
        help='This is the date on which the goods with this Serial Number should be removed from the stock.')
    alert_date = fields.Datetime(default=lambda self: self._get_date('alert_time'),
        help="This is the date on which an alert should be notified about the goods with this Serial Number.")

    # Assign dates according to products data
    @api.model
    def create(self, vals):
        lot_rec = super(StockProductionLot, self).create(vals)
        towrite = []
        for field in ('life_date', 'use_date', 'removal_date', 'alert_date'):
            if not getattr(lot_rec, field):
                towrite.append(field)
        lot_rec.write(self.with_context({'product_id': lot_rec.product_id.id}).default_get(towrite))
        return lot_rec


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    removal_date = fields.Datetime(related='lot_id.removal_date', store=True)

    @api.model
    def apply_removal_strategy(self, location, product, qty, domain, removal_strategy):
        if removal_strategy == 'fefo':
            order = 'removal_date, in_date, id'
            return self._quants_get_order(location, product, qty, domain, order)
        return super(StockQuant, self).apply_removal_strategy(location, product, qty, domain, removal_strategy)


class Product(models.Model):
    _inherit = 'product.template'

    life_time = fields.Integer(string='Product Life Time',
        help='When a new a Serial Number is issued, this is the number of days before the goods may become dangerous and must not be consumed.')
    use_time = fields.Integer(string='Product Use Time',
        help='When a new a Serial Number is issued, this is the number of days before the goods starts deteriorating, without being dangerous yet.')
    removal_time = fields.Integer(string='Product Removal Time',
        help='When a new a Serial Number is issued, this is the number of days before the goods should be removed from the stock.')
    alert_time = fields.Integer(string='Product Alert Time',
        help='When a new a Serial Number is issued, this is the number of days before an alert should be notified.')
