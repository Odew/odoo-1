# -*- coding: utf-8 -*-

from openerp import models, api


class lunch_cancel_order(models.TransientModel):
    """ lunch cancel meal """
    _name = 'lunch.cancel.order'
    _description = 'Wizard to cancel a meal'

    @api.multi
    def cancel(self):
        order_lines = self.env['lunch.order.line'].browse(self._context.get('active_ids'))
        return order_lines.cancel()
