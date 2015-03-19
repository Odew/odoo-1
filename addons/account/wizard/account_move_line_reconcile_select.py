
from openerp import models, fields, api, _


class AccountMoveLineReconcileSelect(models.TransientModel):
    _name = "account.move.line.reconcile.select"
    _description = "Move line reconcile select"

    account_id = fields.Many2one('account.account', string='Account',
        domain = [('reconcile', '=', 1), ('deprecated', '=', False)], required=True)

    @api.multi
    def action_open_window(self):
        """
        This function Open  account move line window for reconcile on given account id
        @return: dictionary of  Open  account move line window for reconcile on given account id

         """
        return {
            'domain': "[('account_id', '=', %d), ('reconciled', '=', False), ('state', '!=', 'draft')]" % self.account_id.id,
            'name': _('Reconciliation'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window'
        }
