# -*- coding: utf-8 -*-

import datetime
from openerp import models, fields, api, _

class lunch_order(models.Model):
    """
    lunch order (contains one or more lunch order line(s))
    """
    _name = 'lunch.order'
    _description = 'Lunch Order'
    _order = 'date desc'

    @api.multi
    def name_get(self):
        return [(order.id, "%s %s" % (_('Lunch Order'), order.id)) for order in self]

    @api.multi
    def _default_alerts_get(self):
        """
        get the alerts to display on the order form
        """
        alert_msg = [alert.get_alert_message()
                     for alert in self.env['lunch.alert'].search([])
                     if alert.get_alert_message()]
        return '\n'.join(alert_msg)

    @api.multi
    def _compute_alerts_get(self):
        """
        get the alerts to display on the order form
        """
        for order in self:
            if order.state == 'new':
                order.alerts = self._default_alerts_get()

    @api.multi
    def _default_get_previous_order_ids(self):
        prev_order = self.env['lunch.order.line']
        prev_order_res = prev_order.search([('user_id', '=', self.env.uid)], limit=20 ,order='id desc')

#        return prev_order_res.ids

        # If we return return prev_order_res.ids, we will have duplicates.
        # Therefore, this following part removes duplicates based on product_id and note.
        prev_order_clean = []

        for order in prev_order_res:
            dup = False
            for order_dup in prev_order_clean:
                if (order.product_id == order_dup.product_id) and (order.note == order_dup.note):
                    dup = True
                    break
            if dup == False:
                prev_order_clean.append(order)

        return [ order.id for order in prev_order_clean ]


    @api.multi
    def _compute_get_previous_order_ids(self):
        for order in self:
            order.previous_order_ids = order._default_get_previous_order_ids()

    @api.multi
    @api.depends('order_line_ids')
    def _compute_total(self):
        """
        get and sum the order lines' price
        """
        for order in self:
            order.total = sum(
                orderline.price for orderline in order.order_line_ids)

    @api.multi
    def update_order_state(self):
        """
        Update the state of lunch.order based on its orderlines
        """
        for order in self:
            isconfirmed = True
            for orderline in order.order_line_ids:
                if orderline.state == 'new':
                    isconfirmed = False
                if orderline.state == 'cancelled':
                    isconfirmed = False
                    order.state = 'partially'
            if isconfirmed:
                order.state = 'confirmed'


    user_id = fields.Many2one('res.users', 'User Name', required=True, readonly=True,
                              states={'new': [('readonly', False)]},
                              default=lambda self: self.env.uid)

    date = fields.Date('Date', required=True, readonly=True,
                       states={'new': [('readonly', False)]},
                       default = fields.Date.context_today)

    order_line_ids = fields.One2many('lunch.order.line', 'order_id', 'Products',
                                     ondelete="cascade", readonly=True, copy=True,
                                     states={'new':[('readonly', False)]})

    total = fields.Float(compute='_compute_total', string="Total", store=True)

    state = fields.Selection([('new', 'New'),
                              ('confirmed', 'Confirmed'),
                              ('cancelled', 'Cancelled'),
                              ('partially', 'Partially Confirmed')],
                             'Status', readonly=True, select=True, copy=False, default='new')

    alerts = fields.Text(compute='_compute_alerts_get', string="Alerts",
                         default=_default_alerts_get)

    previous_order_ids = fields.One2many(comodel_name='lunch.order.line',
                                         compute='_compute_get_previous_order_ids',
                                         default=_default_get_previous_order_ids)

    company_id = fields.Many2one('res.company', related='user_id.company_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)


class lunch_order_line(models.Model):
    """
    lunch order line: one lunch order can have many order lines
    """
    _name = 'lunch.order.line'
    _description = 'lunch order line'

    @api.onchange('product_id')
    def onchange_price(self):
        self.price = self.product_id.price

    @api.multi
    def order(self):
        """
        The order_line is ordered to the supplier but isn't received yet
        """
        self.write({'state': 'ordered'})
        orders = self.env['lunch.order'].search(
            [('order_line_ids', 'in', self.ids)])
        return orders.update_order_state()

    @api.multi
    def confirm(self):
        """
        confirm one or more order line, update order status and create new cashmove
        """
        for orderline in self:
            if orderline.state != 'confirmed':
                values = {
                    'user_id': orderline.user_id.id,
                    'amount': -orderline.price,
                    'description': orderline.product_id.name,
                    'order_id': orderline.id,
                    'state': 'order',
                    'date': orderline.date,
                }
                self.env['lunch.cashmove'].create(values)
                orderline.state = 'confirmed'
        orders = self.env['lunch.order'].search(
            [('order_line_ids', 'in', self.ids)])
        return orders.update_order_state()

    @api.multi
    def cancel(self):
        """
        cancel one or more order.line, update order status and unlink existing cashmoves
        """
        self.write({'state': 'cancelled'})
        for orderline in self:
            orderline.cashmove.unlink()
        orders = self.env['lunch.order'].search(
            [('order_line_ids', 'in', self.ids)])
        return orders.update_order_state()


    name = fields.Char(string='name', related='product_id.name', readonly=True)

    order_id = fields.Many2one('lunch.order', 'Order', ondelete='cascade')

    product_id = fields.Many2one('lunch.product', 'Product', required=True)

    category_id = fields.Many2one('lunch.product.category', string='Product Category',
                                  related='product_id.category_id', readonly=True, store=True)

    date = fields.Date(string='Date', related='order_id.date', readonly=True, store=True)

    supplier = fields.Many2one('res.partner', string='Supplier', related='product_id.supplier',
                               readonly=True, store=True)

    user_id = fields.Many2one('res.users', string='User', related='order_id.user_id',
                              readonly=True, store=True)

    note = fields.Text('Note')
    price = fields.Float('Price')
    state = fields.Selection([('new', 'New'),
                              ('confirmed', 'Received'),
                              ('ordered', 'Ordered'),
                              ('cancelled', 'Cancelled')],
                             'Status', readonly=True, select=True, default='new')

    cashmove = fields.One2many('lunch.cashmove', 'order_id', 'Cash Move')
    currency_id = fields.Many2one('res.currency', related='order_id.currency_id')


class lunch_product(models.Model):
    """
    lunch product
    """
    _name = 'lunch.product'
    _description = 'lunch product'

    name = fields.Char('Product', required=True)
    category_id = fields.Many2one('lunch.product.category', 'Category', required=True)
    description = fields.Text('Description')
    price = fields.Float('Price', digits=(16, 2))
    supplier = fields.Many2one('res.partner', 'Supplier')


class lunch_product_category(models.Model):
    """
    lunch product category
    """
    _name = 'lunch.product.category'
    _description = 'lunch product category'

    # such as PIZZA, SANDWICH, PASTA, CHINESE, BURGER, ...
    name = fields.Char('Category', required=True)


class lunch_cashmove(models.Model):
    """
    lunch cashmove => order or payment
    """
    _name = 'lunch.cashmove'
    _description = 'lunch cashmove'

    @api.multi
    def name_get(self):
        return [(cashmove.id, "%s %s" % (_('Lunch Cashmove'), cashmove.id)) for cashmove in self]

    user_id = fields.Many2one('res.users', 'User Name', required=True,
                              default=lambda self: self.env.uid)

    date = fields.Date('Date', required=True, default=fields.Date.context_today)

    amount = fields.Float('Amount', required=True) # Can be positive or negative

    description = fields.Text('Description') # Can be an order or a payment

    order_id = fields.Many2one('lunch.order.line', 'Order', ondelete='cascade')

    state = fields.Selection([('order', 'Order'), ('payment', 'Payment')],
                             'Is an order or a Payment', default='payment')


class lunch_alert(models.Model):
    """
    lunch alert
    """
    _name = 'lunch.alert'
    _description = 'Lunch Alert'

    @api.multi
    def name_get(self):
        return [(alert.id, "%s %s" % (_('Alert'), alert.id)) for alert in self]

    @api.model
    def get_alert_message(self):
        """
        This method check if the alert can be displayed today
        if alert type is specific : compare specific_day(date) with today's date
        if alert type is week : check today is set as alert (checkbox true) eg. self['monday']
        if alert type is day : True
        return : Message if can_display_alert is True else False
        """

        can_display_alert = {
            'specific': (self.specific_day == fields.Date.context_today(self)),
            'week': self[datetime.datetime.now().strftime('%A').lower()],
            'days': True
        }

        if can_display_alert[self.alert_type]:
            mynow = fields.Datetime.context_timestamp(self, datetime.datetime.now())
            hour_to = int(self.end_hour)
            min_to = int((self.end_hour - hour_to) * 60)
            to_alert = datetime.time(hour_to, min_to)
            hour_from = int(self.start_hour)
            min_from = int((self.start_hour - hour_from) * 60)
            from_alert = datetime.time(hour_from, min_from)
            if from_alert <= mynow.time() <= to_alert:
                return self.message
        return False

    message = fields.Text('Message', required=True)

    alert_type = fields.Selection([('specific', 'Specific Day'),
                                   ('week', 'Every Week'),
                                   ('days', 'Every Day')],
                                  string='Recurrency', required=True, select=True, default='specific')

    specific_day = fields.Date('Day', default=fields.Date.context_today)

    monday = fields.Boolean('Monday')
    tuesday = fields.Boolean('Tuesday')
    wednesday = fields.Boolean('Wednesday')
    thursday = fields.Boolean('Thursday')
    friday = fields.Boolean('Friday')
    saturday = fields.Boolean('Saturday')
    sunday = fields.Boolean('Sunday')

    start_hour = fields.Float('Between', oldname='active_from', required=True, default=7)
    end_hour = fields.Float('And', oldname='active_to', required=True, default=23)
