# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request

class WebsiteHr(http.Controller):

    @http.route(['/page/website.aboutus', '/page/aboutus'], type='http', auth="public", website=True)
    def aboutus(self, **post):
        if request.env['res.users'].has_group('base.group_website_publisher'):
            employees = request.env['hr.employee'].search([])
        else:
            employees = request.env['hr.employee'].search([('website_published', '=', True)])
        values = {
            'employee_ids': employees
        }
        return request.website.render("website.aboutus", values)
