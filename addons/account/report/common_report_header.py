# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models,api
from openerp.tools.translate import _

class common_report_header(object):

    @api.multi
    def _sum_debit(self, date=False, journal_id=False):
        if journal_id and isinstance(journal_id, int):
            journal_id = [journal_id]
        if date and isinstance(date, int):
            date = date
        if not journal_id:
            journal_id = self.journal_ids
        if not date:
            date = self.date
        if not (date and journal_id):
            return 0.0
        self._cr.execute('SELECT SUM(debit) FROM account_move_line l '
                        'WHERE date = %s AND journal_id IN %s ' + self.query_get_clause + ' ',
                        (date, tuple(journal_id)))
        return self._cr.fetchone()[0] or 0.0

    @api.multi
    def _sum_credit(self, date=False, journal_id=False):
        if journal_id and isinstance(journal_id, int):
            journal_id = [journal_id]
        if date and isinstance(date, int):
            date = date
        if not journal_id:
            journal_id = self.journal_ids
        if not date:
            date = self.date
        if not (date and journal_id):
            return 0.0
        self._cr.execute('SELECT SUM(credit) FROM account_move_line l '
                        'WHERE date = %s AND journal_id IN %s '+ self.query_get_clause+'',
                        (date, tuple(journal_id)))
        return self._cr.fetchone()[0] or 0.0

    @api.model
    def _get_start_date(self, data):
        if data.get('form', False) and data['form'].get('date_from', False):
            return data['form']['date_from']
        elif data.get('form', False) and data['form'].get('period_from', False):
            return data['form']['period_from']
        return ''

    @api.model
    def _get_target_move(self, data):
        if data.get('form', False) and data['form'].get('target_move', False):
            if data['form']['target_move'] == 'all':
                return _('All Entries')
            return _('All Posted Entries')
        return ''

    @api.model
    def _get_end_date(self, data):
        if data.get('form', False) and data['form'].get('date_to', False):
            return data['form']['date_to']
        elif data.get('form', False) and data['form'].get('period_to', False):
            return data['form']['period_to']
        return ''

    @api.model
    def _get_account(self, data):
        if data.get('form', False) and data['form'].get('chart_account_id', False):
            return self.env['account.account'].browse(data['form']['chart_account_id']).name
        return ''

    @api.model
    def _get_sortby(self, data):
        raise (_('Error!'), _('Not implemented.'))

    @api.model
    def _get_filter(self, data):
        if data.get('form', False) and data['form'].get('filter', False):
            if data['form']['filter'] == 'filter_date':
                return self._translate('Date')
            elif data['form']['filter'] == 'filter_period':
                return self._translate('Periods')
        return self._translate('No Filters')

    @api.multi
    def _sum_debit_period(self, date, journal_id=None):
        journals = journal_id or self.journal_ids
        if not journals:
            return 0.0
        self._cr.execute('SELECT SUM(debit) FROM account_move_line l '
                        'WHERE date=%s AND journal_id IN %s '+ self.query_get_clause +'',
                        (date, tuple(journals)))
        return self._cr.fetchone()[0] or 0.0

    @api.multi
    def _sum_credit_period(self, date, journal_id=None):
        journals = journal_id or self.journal_ids
        if not journals:
            return 0.0
        self.cr.execute('SELECT SUM(credit) FROM account_move_line l '
                        'WHERE date=%s AND journal_id IN %s ' + self.query_get_clause +' ',
                        (date, tuple(journals)))
        return self.cr.fetchone()[0] or 0.0

    @api.model
    def _get_fiscalyear(self, data):
        if data.get('form', False) and data['form'].get('fiscalyear_id', False):
            return self.env['account.fiscalyear'].browse(data['form']['fiscalyear_id']).name
        return ''

    @api.model
    def _get_company(self, data):
        if data.get('form', False) and data['form'].get('chart_account_id', False):
            return self.pool.get('account.account').browse(self.cr, self.uid, data['form']['chart_account_id']).company_id.name
        return ''

    @api.model
    def _get_journal(self, data):
        codes = []
        if data.get('form', False) and data['form'].get('journal_ids', False):
            codes = [x.code for x in self.env['account.journal'].browse(data['form']['journal_ids'])]
        return codes

    @api.model
    def _get_currency(self, data):
        if data.get('form', False) and data['form'].get('chart_account_id', False):
            return self.pool.get('account.account').browse(self.cr, self.uid, data['form']['chart_account_id']).company_id.currency_id.symbol
        return ''

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: