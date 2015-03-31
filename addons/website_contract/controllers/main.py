# -*- coding: utf-8 -*-
import hashlib
import werkzeug

from openerp import http
from openerp.http import request
from openerp import tools
from openerp.tools import plaintext2html
from openerp.tools.translate import _

from openerp.addons.website_portal.controllers.main import website_account


class website_account(website_account):
    @http.route(['/account'], type='http', auth="user", website=True)
    def account(self):
        """ Add contract details to main account page """
        response = super(website_account, self).account()
        partner = request.env.user.partner_id
        account_res = request.env['account.analytic.account']
        cust_accounts = account_res.search([
            '&',
            '|',
            ('partner_id.id', '=', partner.id),
            ('partner_id.id', '=', partner.commercial_partner_id.id),
            ('state', '!=', 'cancelled')
            ])
        response.qcontext.update({'cust_accounts': cust_accounts})

        return response


class website_contract(http.Controller):
    @http.route(['/account/contract/<int:account_id>/',
                 '/account/contract/<int:account_id>/<string:uuid>'], type='http', auth="public", website=True)
    def contract(self, account_id, uuid=None):
        request.env['res.users'].browse(request.uid).has_group('base.group_sale_salesman')
        account_res = request.env['account.analytic.account']
        if uuid:
            account_cust = account_res.sudo().browse(account_id)
            if uuid != account_cust.uuid:
                return request.render("website.404")
            if request.uid == account_cust.partner_id.user_id.id:
                account_cust = account_res.browse(account_id)
        else:
            account_cust = account_res.browse(account_id)
  
        acquirers = request.env['payment.acquirer'].search([('website_published', '=', True)])
        acc_pm = account_cust.payment_method_id
        part_pms = account_cust.partner_id.payment_method_ids
        part_def_pm = account_cust.partner_id.default_payment_method_id
        inactive_options = account_cust.sudo().recurring_inactive_lines
        display_close = account_cust.template_id.sudo().user_closable and account_cust.state != 'close'
        active_plan = account_cust.template_id.sudo()
        values = {
            'account': account_cust,
            'display_close': display_close,
            'inactive_options': inactive_options,
            'active_plan': active_plan,
            'user': request.env.user,
            'acquirers': acquirers,
            'acc_pm': acc_pm,
            'part_pms': part_pms,
            'part_def_pm': part_def_pm,
            'is_salesman': request.env['res.users'].sudo(request.uid).has_group('base.group_sale_salesman'),
        }
        values.update({
            'acquirers': [{'id': acquirer.id, 'name': acquirer.name, 'template': acquirer.s2s_render(account_cust.partner_id.id, values)[0]} for acquirer in acquirers]
        })
        return request.website.render("website_contract.contract", values)

    @http.route(['/account/contract/payment/<int:account_id>/',
                 '/account/contract/payment/<int:account_id>/<string:uuid>'], type='http', auth="public", methods=['POST'], website=True)
    def set_payment_and_pay(self, account_id, uuid=None, **post):
        account_res = request.env['account.analytic.account']
        if uuid:
            account_cust = account_res.sudo().browse(account_id)
            if uuid != account_cust.uuid:
                return request.render("website.404")
        else:
            account_cust = account_res.browse(account_id)

        if post.get('pay_meth'):
            # no change
            if int(post.get('pay_meth')) == -2:
                pass
            # partner default
            elif int(post.get('pay_meth')) == 0:
                account_cust.payment_method_id = account_cust.partner_id.default_payment_method_id
            else:
                account_cust.payment_method_id = int(post['pay_meth'])

        if post.get('pay_now'):
            account_cust._recurring_create_invoice()

        return request.redirect('/account/contract/' + str(account_cust.id) + '/' + str(account_cust.uuid))

    @http.route(['/account/contract/<int:account_id>/change'], type='http', auth="public", website=True)
    def change_contract(self, account_id, uuid, **post):
        account_res = request.env['account.analytic.account']
        account_cust = account_res.sudo().browse(account_id)
        if uuid != account_cust.uuid:
            return request.render("website.404")
        if account_cust.state == 'close':
            return request.redirect('/account/contract/'+str(account_id))
        if post.get('new_template_id'):
            new_template_id = int(post.get('new_template_id'))
            new_template = account_res.browse(new_template_id)
            periods = {'daily': 'Day(s)', 'weekly': 'Week(s)', 'monthly': 'Month(s)', 'yearly': 'Year(s)'}
            msg_before = [account_cust.sudo().template_id.name,
                          str(account_cust.recurring_total),
                          str(account_cust.recurring_interval) + ' ' + str(periods[account_cust.recurring_rule_type])]
            account_cust.sudo().change_subscription(new_template_id)
            msg_after = [account_cust.sudo().template_id.name,
                         str(account_cust.recurring_total),
                         str(account_cust.recurring_interval) + ' ' + str(periods[account_cust.recurring_rule_type])]
            msg_body = ("<div>&nbsp;&nbsp;&bull; <b>" + _('Template') + "</b>: " + msg_before[0] + " &rarr; " + msg_after[0] + "</div>" +
                        "<div>&nbsp;&nbsp;&bull; <b>" + _('Recurring Price') + "</b>: " + msg_before[1] + " &rarr; " + msg_after[1] + "</div>" +
                        "<div>&nbsp;&nbsp;&bull; <b>" + _('Invoicing Period') + "</b>: " + msg_before[2] + " &rarr; " + msg_after[2] + "</div>")
            # price options are about to change and are not propagated to existing sale order: reset the SO
            order = request.website.sudo().sale_get_order()
            if order:
                order.reset_project_id()
            account_cust.message_post(body=msg_body)
            return request.redirect('/account/contract/'+str(account_cust.id)+'/'+str(account_cust.uuid))
        account_templates = account_res.sudo().search([
            ('type', '=', 'template'),
            ('parent_id', '=', account_cust.template_id.sudo().parent_id.id)
        ])
        values = {
            'account': account_cust,
            'active_template': account_cust.template_id,
            'inactive_templates': account_templates,
            'user': request.env.user,
        }
        return request.website.render("website_contract.change_template", values)

    @http.route(['/account/contract/<int:account_id>/close'], type='http', methods=["POST"], auth="public", website=True)
    def close_account(self, account_id, uuid=None, **post):
        account_res = request.env['account.analytic.account']

        if uuid:
            account_cust = account_res.sudo().browse(account_id)
            if uuid != account_cust.uuid:
                return request.render("website.404")
        else:
            account_cust = account_res.browse(account_id)

        if account_cust.sudo().template_id.user_closable and post.get('confirm_close'):
            if post.get('closing_reason'):
                account_cust.closing_reason = post.get('closing_reason')
                account_cust.message_post('Closing reason : ' + account_cust.closing_reason)
            account_cust.set_close()
        return request.redirect('/account')

    @http.route(['/account/contract/<int:account_id>/add_option'], type='http', methods=["POST"], auth="public", website=True)
    def add_option(self, account_id, uuid=None, **post):
        option_res = request.env['account.analytic.invoice.line.option']
        account_res = request.env['account.analytic.account']
        if uuid:
            account_cust = account_res.sudo().browse(account_id)
            if uuid != account_cust.uuid:
                return request.render("website.404")
        else:
            account_cust = account_res.browse(account_id)
        new_option_id = int(post.get('new_option_id'))
        new_option = option_res.sudo().browse(new_option_id)
        if not new_option.price_unit or not new_option.price_unit*account_cust.partial_recurring_invoice_ratio():
            account_cust.sudo().add_option(new_option_id)
            account_cust.message_post(body=_("""
            <div>Option added by customer</div>
            <div>&nbsp;&nbsp;&bull; <b>Option</b>: """)+new_option.product_id.name_template+_("""</div>
            <div>&nbsp;&nbsp;&bull; <b>Price</b>: """)+str(new_option.price_unit)+_("""</div>
            <div>&nbsp;&nbsp;&bull; <b>Sale Order</b>: None</div>"""))
        return request.redirect('/account/contract/'+str(account_id)+('/'+str(account_cust.uuid) if uuid else None))

    @http.route(['/account/contract/<int:account_id>/remove_option'], type='http', methods=["POST"], auth="public", website=True)
    def remove_option(self, account_id, uuid=None, **post):
        remove_option_id = int(post.get('remove_option_id'))
        option_res = request.env['account.analytic.invoice.line.option']
        account_res = request.env['account.analytic.account']
        if uuid:
            remove_option = option_res.sudo().browse(remove_option_id)
            account_cust = account_res.sudo().browse(account_id)
            if uuid != account_cust.uuid:
                return request.render("website.404")
        else:
            remove_option = option_res.browse(remove_option_id)
            account_cust = account_res.browse(account_id)
        if remove_option.portal_access != "both" and not request.env.user.has_group('base.group_sale_salesman'):
            return request.render("website.403")
        account_cust.sudo().remove_option(remove_option_id)
        account_cust.message_post(body=_("""
            <div>Option removed by customer</div>
            <div>&nbsp;&nbsp;&bull; <b>Option</b>: """)+remove_option.product_id.sudo().name_template+_("""</div>
            <div>&nbsp;&nbsp;&bull; <b>Price</b>: """)+str(remove_option.price_unit)+"""</div>""")
        return request.redirect('/account/contract/'+str(account_id)+('/'+str(account_cust.uuid) if uuid else None))

    @http.route(['/account/contract/<int:account_id>/pay_option'], type='http', methods=["POST"], auth="public", website=True)
    def pay_option(self, account_id, **post):
        order = request.website.sale_get_order(force_create=True)
        order.set_project_id(account_id)
        new_option_id = int(post.get('new_option_id'))
        new_option = request.env['account.analytic.invoice.line.option'].sudo().browse(new_option_id)
        account_cust = request.env['account.analytic.account'].browse(account_id)
        account_cust.sudo().partial_invoice_line(order, new_option)

        return request.redirect("/shop/cart")
