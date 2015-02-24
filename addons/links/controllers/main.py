# -*- coding: utf-8 -*-
import werkzeug

from openerp.addons.web import http
from openerp.http import request


class Links(http.Controller):

    @http.route('/r/<string:code>', type='http', auth='none', website=True)
    def full_url_redirect(self, code, **post):
        request.env['links.click'].add_click(code, request.httprequest.remote_addr, request.session['geoip'].get('country_code'), stat_id=False)
        redirect_url = request.env['links'].get_url_from_code(code)
        return werkzeug.utils.redirect(redirect_url or '', 301)
