# -*- coding: utf-8 -*-

from openerp import models, api


class lunch_confirm_order(models.TransientModel):
    """ lunch confirm meal """
    _name = 'lunch.confirm.order'
    _description = 'Wizard to confirm a meal'

    @api.multi
    def confirm(self):
        order_lines = self.env['lunch.order.line'].browse(self._context.get('active_ids'))
        return order_lines.confirm()
