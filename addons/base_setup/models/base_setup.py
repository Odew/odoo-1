# -*- coding: utf-8 -*-

from openerp import _, api, fields, models


# Specify Your Terminology will move to 'partner' module
class SpecifyPartnerTerminolgy(models.TransientModel):
    _name = 'base.setup.terminology'
    _inherit = 'res.config'

    partner = fields.Selection([
        ('Customer', 'Customer'),
        ('Client', 'Client'),
        ('Member', 'Member'),
        ('Patient', 'Patient'),
        ('Partner', 'Partner'),
        ('Donor', 'Donor'),
        ('Guest', 'Guest'),
        ('Tenant', 'Tenant')], string='How do you call a Customer',
        required=True,
        default='Customer')

    def make_translations(self, name, type, src, value, res_id=0):
        IrTranslation = self.env['ir.translation']
        UserLang = self.env.user.lang
        existing_translations = IrTranslation.search([
            ('name', '=', name),
            ('lang', '=', UserLang),
            ('type', '=', type),
            ('src', '=', src),
            ('res_id', '=', res_id)])
        if existing_translations:
            existing_translations.write({'value': value})
        else:
            IrTranslation.create({'name': name, 'lang': UserLang, 'type': type, 'src': src, 'value': value, 'res_id': res_id})
        return {}

    @api.multi
    def execute(self):
        def _case_insensitive_replace(ref_string, src, value):
            import re
            pattern = re.compile(src, re.IGNORECASE)
            return pattern.sub(_(value), _(ref_string))
        IrModelFields = self.env['ir.model.fields']
        IrUiMenu = self.env['ir.ui.menu']
        IrActionsActWindow = self.env['ir.actions.act_window']
        # translate label of field
        for field in IrModelFields.search([('field_description', 'ilike', 'Customer')]):
            field_ref = field.model_id.model + ',' + field.name
            self.make_translations(field_ref, 'field', field.field_description, _case_insensitive_replace(
                field.field_description, 'Customer', self.partner))
        # translate help tooltip of field
        for obj in self.pool.models.values():
            for field_name, field_rec in obj._columns.items():
                if field_rec.help.lower().count('customer'):
                    field_ref = obj._name + ',' + field_name
                    self.make_translations(field_ref, 'help', field_rec.help, _case_insensitive_replace(
                        field_rec.help, 'Customer', self.partner))
        # translate menuitems
        for menu in IrUiMenu.search([('name', 'ilike', 'Customer')]):
            menu_ref = 'ir.ui.menu' + ',' + 'name'
            self.make_translations(menu_ref, 'model', menu.name, _case_insensitive_replace(
                menu.name, 'Customer', self.partner), res_id=menu.id)
        # translate act window name
        for action in IrActionsActWindow.search([('name', 'ilike', 'Customer')]):
            action_ref = 'ir.actions.act_window' + ',' + 'name'
            self.make_translations(action_ref, 'model', action.name, _case_insensitive_replace(
                action.name, 'Customer', self.partner), res_id=action.id)
        # translate act window tooltips
        for action in IrActionsActWindow.search([('help', 'ilike', 'Customer')]):
            action_ref = 'ir.actions.act_window' + ',' + 'help'
            self.make_translations(action_ref, 'model', action.help, _case_insensitive_replace(
                action.help, 'Customer', self.partner), res_id=action.id)
        return {}
