from openerp.osv import fields, osv


class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _columns = {
        'default_payment_method_id': fields.many2one('payment.method', 'Default Payment Method', help="Default Payment Method to use for payments", domain="[('partner_id', '=', id)]"),
        'payment_method_ids': fields.one2many('payment.method', 'partner_id', 'Payment Methods'),
    }
