# -*- coding: utf-8 -*-

import re

from openerp import api, fields, models


class BaseConfigSettings(models.TransientModel):
    _name = 'base.config.settings'
    _inherit = 'res.config.settings'

    module_multi_company = fields.Boolean(string='Manage multiple companies',
            help='Work in multi-company environments, with appropriate security access between companies.\n'
                 '-This installs the module multi_company.')
    module_share = fields.Boolean(
        string='Allow documents sharing',
        help='Share or embbed any screen of Odoo.')
    module_portal = fields.Boolean(
        string='Activate the customer portal',
        help='Give your customers access to their documents.')
    module_auth_oauth = fields.Boolean(string='Use external authentication providers, sign in with google, facebook, ...')
    module_base_import = fields.Boolean(string="Allow users to import data from CSV files")
    module_google_drive = fields.Boolean(
        string='Attach Google documents to any record',
        help='This installs the module google_docs.')
    module_google_calendar = fields.Boolean(
        string='Allow the users to synchronize their calendar with Google Calendar',
        help='This installs the module google_calendar.')
    font = fields.Many2one('res.font', string="Report Font",
        domain=[('mode', 'in', ('Normal', 'Regular', 'all', 'Book'))],
        help="Set the font into the report header, it will be used as default font in the RML reports of the user company",
        default=lambda self: self.env.user.company_id.font.id)
    module_inter_company_rules = fields.Boolean(string='Manage Inter Company',
        help="This installs the module inter_company_rules.\n Configure company rules to automatically create SO/PO when one of your company sells/buys to another of your company.")
    company_share_partner = fields.Boolean(string='Share partners to all companies',
        help="Share your partners to all companies defined in your instance.\n"
             " * Checked : Partners are visible for every companies, even if a company is defined on the partner.\n"
             " * Unchecked : Each company can see only its partner (partners where company is defined). Partners not related to a company are visible for all companies.")

    @api.multi
    def open_company(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Your Company',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.company',
            'res_id': self.env.user.company_id.id,
            'target': 'current',
        }

    @staticmethod
    def _change_header(header, font):
        """ Replace default fontname use in header and setfont tag """
        default_para = re.sub('fontName.?=.?".*"', 'fontName="%s"' % font, header)
        return re.sub('(<setFont.?name.?=.?)(".*?")(.)', '\g<1>"%s"\g<3>' % font, default_para)

    @api.one
    def set_base_defaults(self):
        if self.font:
            User = self.env.user
            font_name = self.font.name
            User.company_id.write({
                'font': self.font.id,
                'rml_header': self._change_header(User.company_id.rml_header, font_name),
                'rml_header2': self._change_header(User.company_id.rml_header2, font_name),
                'rml_header3': self._change_header(User.company_id.rml_header3, font_name)})
        return {}

    @api.multi
    def act_discover_fonts(self):
        return self.env["res.font"].font_scan()

    @api.multi
    def get_default_company_share_partner(self):
        partner_rule = self.env.ref('base.res_partner_rule')
        return {
            'company_share_partner': not bool(partner_rule.active)
        }

    @api.multi
    def set_default_company_share_partner(self):
        partner_rule = self.env.ref('base.res_partner_rule')
        for wizard in self:
            self.env['ir.rule'].browse(partner_rule.id).write(
                {'active': not bool(wizard.company_share_partner)})


# Preferences wizard for Sales & CRM.
# It is defined here because it is inherited independently in modules sale, crm.
class SaleConfigSettings(models.TransientModel):
    _name = 'sale.config.settings'
    _inherit = 'res.config.settings'

    module_web_linkedin = fields.Boolean(string='Get contacts automatically from linkedIn',
        help="When you create a new contact (person or company), you will be able to load all the data from LinkedIn (photos, address, etc).")
    module_crm = fields.Boolean(string='CRM')
    module_sale = fields.Boolean(string='SALE')
