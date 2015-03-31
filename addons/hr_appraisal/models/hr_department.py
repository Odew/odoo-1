# -*- coding: utf-8 -*-
from openerp import api, fields, models, _


class hr_department(models.Model):
    _inherit = 'hr.department'

    @api.multi
    def action_number_of_answers(self):
        self.ensure_one()
        action_hr_evaluation = self.env.ref('hr_appraisal.hr_appraisal_action_from_department').read()[0]
        action_hr_evaluation['display_name'] = _('Appraisal to Process')
        action_hr_evaluation['domain'] = str([('id', 'in', self.to_process_appraisal_ids.ids)])
        return action_hr_evaluation

    to_process_appraisal_ids = fields.One2many('hr.appraisal', 'department_id', domain=['&', ('state', '=', 'pending'), '|', ('date_close', '<=', fields.Datetime.now()), ('user_input_ids.state', '=', 'done')], string='Appraisal to Process')
    to_start_appraisal_ids = fields.One2many('hr.appraisal', 'department_id', domain=[('state', '=', 'new')], string='Appraisal to Start')
