# -*- coding: utf-8 -*-
import werkzeug

from openerp import http
from openerp.http import request
from openerp import tools
from openerp.tools.translate import _


class website_payment(http.Controller):
    @http.route(['/payment'], type='http', auth="user", website=True)
    def account(self, **post):
        acquirers = request.env['payment.acquirer'].search([('website_published', '=', True)])
        values = {
            'acquirers': list({'id': acquirer.id, 'name': acquirer.name, 'template': acquirer.s2s_render(request.env.user.partner_id.id, {'return_success': "/account"})[0]} for acquirer in acquirers),
            'error': {},
            'error_message': []
        }
        
        if post:
            acquirer_id = post.get('acquirer_id')
            acquirer = request.env['payment.acquirer'].browse(acquirer_id)
            redirect = acquirer.s2s_process(post, success_redirect="/account", fail_redirect="/account")
            return request.redirect(redirect)

        return request.website.render("website_payment.cc_form", values)

    @http.route(['/account/payment_method'], type='http', auth="user", website=True)
    def payment_method(self, **post):
        acquirers = request.env['payment.acquirer'].search([('website_published', '=', True), ('s2s_support', '=', True)])
        partner = request.env.user.partner_id
        payment_methods = partner.payment_method_ids
        default_pm = partner.default_payment_method_id
        pms = []
        for pay_meth in payment_methods:
            pms.append({
                'name': pay_meth.name,
                'id': pay_meth.id
            })
        values = {
            'pms': pms,
            'def_pm': dict(name=default_pm.name, id=default_pm.id),
            'error': {},
            'error_message': []
        }
        if post:
            post_acquirer_id = int(post.get('pm_acquirer_id'))
            post_acquirer = request.env['payment.acquirer'].browse(post_acquirer_id)
            if post.get('cc_number'):
                error, error_message = self.validate_payment_method(post)
                values.update({'error': error, 'error_message': error_message})
                if not error:
                    data = {
                        'cc_number': post.get('cc_number'),
                        'cc_cvc': int(post.get('cc_cvc')),
                        'cc_holder_name': post.get('cc_holder_name'),
                        'cc_expiry': post.get('cc_expiry'),
                        'cc_brand': post.get('cc_brand'),
                        'acquirer_id': int(post.get('cc_acquirer') or acquirers[0].id),
                        'partner_id': int(request.env.user.partner_id.id)
                    }
                    pm_id = request.env['payment.method'].sudo().create(data)
                    if post.get('cc_default'):
                        partner.default_payment_method_id = pm_id
                    return request.redirect('/account')
            elif post.get('default_pm') != partner.default_payment_method_id:
                partner.default_payment_method_id = int(post.get('default_pm'))
                return request.redirect('/account')
        
        init_values = values.update({'return_success': '/account/payment_method'})
        values['acquirers'] = list({
            'id': acquirer.id,
            'name': acquirer.name,
            'template': acquirer.s2s_render(request.env.user.partner_id.id, values)[0]
        } for acquirer in acquirers)

        return request.website.render("website_payment.pay_methods", values)

    @http.route(['/account/payment_method/delete/<int:payment_method_id>'], type='http', auth="user", website=True)
    def delete(self, payment_method_id):
        pay_meth = request.env['payment.method'].browse(payment_method_id)
        pay_meth.active = False
        return request.redirect('/account/payment_method')
