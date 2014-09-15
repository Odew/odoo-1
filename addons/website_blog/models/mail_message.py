# -*- coding: utf-8 -*-

from openerp import fields, models


class MailMessage(models.Model):
    _inherit = 'mail.message'

    path = fields.Char(string="Discussion Path", select=True, help='Used to display messages in a paragraph-based chatter using a unique path;')
