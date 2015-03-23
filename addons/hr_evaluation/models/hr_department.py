# -*- coding: utf-8 -*-
import datetime

from openerp import api, fields, models


class hr_department(models.Model):
    _inherit = 'hr.department'

    @api.one
    def _compute_appraisal(self):
        self.evaluation_ids = self.env['hr_evaluation.evaluation'].search([('employee_id.department_id', '=', self.id)])

    def _to_approve_appraisal_filter(self, appraisal):
        current_date = datetime.datetime.now()
        return appraisal.state == 'pending' and (fields.Datetime.from_string(appraisal.date_close) <= current_date or appraisal.completed_user_input_count > 0)

    @api.one
    def _compute_appraisal_process(self):
        appraisal_to_process = self.evaluation_ids.filtered(self._to_approve_appraisal_filter)
        self.appraisal_to_process_count = len(appraisal_to_process)

    @api.one
    def _compute_appraisal_to_start(self):
        self.appraisal_to_start_count = len(self.evaluation_ids.filtered(lambda r: r.state == 'new'))

    @api.multi
    def action_number_of_answers(self):
        self.ensure_one()
        action_hr_evaluation = self.env.ref('hr_evaluation.hr_appraisal_action_from_department').read()[0]
        appraisal_process = self.evaluation_ids.filtered(self._to_approve_appraisal_filter)
        action_hr_evaluation['display_name'] = 'Appraisal to Process'
        action_hr_evaluation['domain'] = str([('id', 'in', appraisal_process.ids)])
        return action_hr_evaluation

    appraisal_to_start_count = fields.Integer(
        compute='_compute_appraisal_to_start', string='Appraisal to Start')
    appraisal_to_process_count = fields.Integer(
        compute='_compute_appraisal_process', string='Appraisal Process')
    evaluation_ids = fields.One2many('hr_evaluation.evaluation', compute='_compute_appraisal')
