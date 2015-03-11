# -*- coding: utf-8 -*-

from openerp import api, fields, models


class BaseConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    auth_oauth_google_enabled = fields.Boolean(
        string='Allow users to sign in with Google')
    auth_oauth_google_client_id = fields.Char(string='Client ID')
    auth_oauth_facebook_enabled = fields.Boolean(
        string='Allow users to sign in with Facebook')
    auth_oauth_facebook_client_id = fields.Char(string='Client ID')

    @api.model
    def default_get(self, fields):
        res = super(BaseConfigSettings, self).default_get(fields)
        res.update(self.get_oauth_providers(fields))
        return res

    @api.model
    def get_oauth_providers(self, fields):
        google_provider = self.env.ref('auth_oauth.provider_google')
        facebook_provider = self.env.ref('auth_oauth.provider_facebook')
        return {
            'auth_oauth_google_enabled': google_provider.enabled,
            'auth_oauth_google_client_id': google_provider.client_id,
            'auth_oauth_facebook_enabled': facebook_provider.enabled,
            'auth_oauth_facebook_client_id': facebook_provider.client_id,
        }

    @api.multi
    def set_oauth_providers(self):
        google_provider = self.env.ref('auth_oauth.provider_google')
        facebook_provider = self.env.ref('auth_oauth.provider_facebook')
        rg = {
            'enabled': self.auth_oauth_google_enabled,
            'client_id': self.auth_oauth_google_client_id,
        }
        rf = {
            'enabled': self.auth_oauth_facebook_enabled,
            'client_id': self.auth_oauth_facebook_client_id,
        }
        google_provider.write(rg)
        facebook_provider.write(rf)
