# -*- coding: utf-8 -*-
from openerp import http

# class AccountPlaid(http.Controller):
#     @http.route('/account_plaid/account_plaid/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_plaid/account_plaid/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_plaid.listing', {
#             'root': '/account_plaid/account_plaid',
#             'objects': http.request.env['account_plaid.account_plaid'].search([]),
#         })

#     @http.route('/account_plaid/account_plaid/objects/<model("account_plaid.account_plaid"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_plaid.object', {
#             'object': obj
#         })
