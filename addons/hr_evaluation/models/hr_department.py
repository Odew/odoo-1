# -*- coding: utf-8 -*-
import datetime

from openerp import api, fields, models, _


class hr_department(models.Model):
    _inherit = 'hr.department'

    def _to_approve_appraisal_filter(self, appraisal):
        current_date = datetime.datetime.now()
        return fields.Datetime.from_string(appraisal.date_close) <= current_date or appraisal.completed_user_input_count > 0

    @api.one
    def _compute_appraisal_process(self):
        appraisal_to_process = self.to_process_appraisal_ids.filtered(self._to_approve_appraisal_filter)
        self.appraisal_to_process_count = len(appraisal_to_process)

    @api.multi
    def action_number_of_answers(self):
        self.ensure_one()
        action_hr_evaluation = self.env.ref('hr_evaluation.hr_appraisal_action_from_department').read()[0]
        appraisal_process = self.to_process_appraisal_ids.filtered(self._to_approve_appraisal_filter)
        action_hr_evaluation['display_name'] = _('Appraisal to Process')
        action_hr_evaluation['domain'] = str([('id', 'in', appraisal_process.ids)])
        return action_hr_evaluation

    to_process_appraisal_ids = fields.One2many('hr.evaluation', 'department_id', domain=[('state', '=', 'pending')], string='Appraisal to Process')
    to_start_appraisal_ids = fields.One2many('hr.evaluation', 'department_id', domain=[('state', '=', 'new')], string='Appraisal to Start')
    appraisal_to_process_count = fields.Integer(compute='_compute_appraisal_process', string='Appraisal Process')
