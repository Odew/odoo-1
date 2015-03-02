# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request


class GoogleCalendarController(http.Controller):

    @http.route('/google_calendar/sync_data', type='json', auth='user')
    def sync_data(self, arch, fields, model, **kw):
        """
            This route/function is called when we want to synchronize Odoo calendar with Google Calendar
            Function return a dictionary with the status :  need_config_from_admin, need_auth, need_refresh, success if not calendar_event
            The dictionary may contains an url, to allow Odoo Client to redirect user on this URL for authorization for example
        """

        if model == 'calendar.event':
            GsObj = request.env['google.service']
            GcObj = request.env['google.calendar'].with_context(kw.get('local_context'))

            # Checking that admin have already configured Google API for google synchronization !
            client_id = GsObj.get_client_id('calendar')

            if not client_id or client_id == '':
                action = ''
                if GcObj.can_authorize_google():
                    action = request.env.ref('google_calendar.action_config_settings_google_calendar')

                return {
                    "status": "need_config_from_admin",
                    "url": '',
                    "action": action.id
                }

            # Checking that user have already accepted Odoo to access his calendar !
            if GcObj.need_authorize():
                url = GcObj.authorize_google_uri(from_url=kw.get('fromurl'))
                return {
                    "status": "need_auth",
                    "url": url
                }

            # If App authorized, and user access accepted, We launch the synchronization
            return GcObj.synchronize_events()

        return {"status": "success"}

    @http.route('/google_calendar/remove_references', type='json', auth='user')
    def remove_references(self, model, **kw):
        """
            This route/function is called when we want to remove all the references between one calendar Odoo and one Google Calendar
        """
        status = "NOP"
        if model == 'calendar.event':
            GcObj = request.env['google.calendar']
            # Checking that user have already accepted Odoo to access his calendar !
            if GcObj.with_context(kw.get('local_context')).remove_references():
                status = "OK"
            else:
                status = "KO"
        return {"status": status}
