# -*- coding: utf-8 -*-
import werkzeug

from openerp import http
from openerp.http import request
from openerp import tools


class website_payment(http.Controller):
    @http.route(['/payment'], type='http', auth="user", website=True)
    def account(self, **post):
        acquirers = request.env['payment.acquirer'].search([('website_published', '=', True)])
        values = dict(acquirers=list({'id': acquirer.id, 'name': acquirer.name} for acquirer in acquirers))

        if post:
            data = {
                'cc_number': post.get('cc_number'),
                'cc_cvc': int(post.get('cc_cvc')),
                'cc_holder_name': post.get('cc_holder_name'),
                'cc_expiry': post.get('cc_expiry'),
                'cc_brand': post.get('cc_brand'),
                'acquirer_id': int(post.get('cc_acquirer')),
                'partner_id': int(request.env.user.partner_id.id)
            }
            request.env['payment.method'].sudo().create(data)
            return request.redirect('/account')

        return request.website.render("website_payment.cc_form", values)
