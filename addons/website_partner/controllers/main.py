# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
from openerp.addons.website.models.website import unslug


class WebsitePartnerPage(http.Controller):

    # Do not use semantic controller due to SUPERUSER_ID
    @http.route(['/partners/<partner_id>'], type='http', auth="public", website=True)
    def partners_detail(self, partner_id, **post):
        _, partner_id = unslug(partner_id)
        if partner_id:
            partner = request.env['res.partner'].sudo().browse(partner_id)
            is_website_publisher = request.env['res.users'].has_group('base.group_website_publisher')
            if partner.exists() and (partner.website_published or is_website_publisher):
                values = {
                    'main_object': partner,
                    'partner': partner,
                    'edit_page': False
                }
                return request.website.render("website_partner.partner_page", values)
        return request.not_found()
