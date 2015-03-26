# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from openerp import fields
from openerp.tests.common import TransactionCase


class TestHrEvaluation(TransactionCase):
    """ Test used to check that when doing appraisal creation."""

    def setUp(self):
        super(TestHrEvaluation, self).setUp()
        self.HrEmployee = self.env['hr.employee']
        self.HrEvaluation = self.env['hr.evaluation']
        self.main_company = self.env.ref('base.main_company')

    def test_hr_evaluation(self):
        # I create a new Employee with appraisal configuration.
        self.hr_employee = self.HrEmployee.create(dict(
            name="Michael Hawkins",
            department_id=self.env.ref('hr.dep_rd').id,
            parent_id=self.env.ref('hr.employee_al').id,
            job_id=self.env.ref('hr.job_developer').id,
            work_location="Grand-Rosière",
            work_phone="+3281813700",
            work_email='michael@openerp.com',
            appraisal_manager=True,
            appraisal_manager_ids=[self.env.ref('hr.employee_al').id],
            appraisal_manager_survey_id=self.env.ref('survey.feedback_form').id,
            appraisal_colleagues=True,
            appraisal_colleagues_ids=[self.env.ref('hr.employee_stw')],
            appraisal_colleagues_survey_id=self.env.ref('hr_evaluation.opinion_form').id,
            appraisal_self=True,
            appraisal_self_survey_id=self.env.ref('hr_evaluation.appraisal_form').id,
            appraisal_repeat=True,
            appraisal_repeat_number=1,
            appraisal_repeat_delay='year',
            evaluation_date=fields.Date.today()
        ))

        # I run the scheduler
        self.HrEmployee.run_employee_evaluation()  # cronjob

        # I check whether new appraisal is created for above employee or not
        evaluations = self.HrEvaluation.search([('employee_id', '=', self.hr_employee.id)])
        self.assertTrue(evaluations, "Appraisal not created")

        # I check next evaluation date
        self.assertEqual(self.hr_employee.evaluation_date, str(date.today() + relativedelta(years=1)), 'Next appraisal date is wrong')

        # I start the evaluation process by click on "Start Appraisal" button.
        evaluations.write({'date_close': str(date.today() + relativedelta(days=5))})
        evaluations.button_send_appraisal()

        # I check that state is "Appraisal Sent".
        self.assertEqual(evaluations.state, 'pending', "Evaluation should be 'Appraisal Sent' state")
        # I check that "Final Interview Date" is set or not.
        evaluations.write({'interview_deadline': str(date.today() + relativedelta(months=1))})
        self.assertTrue(evaluations.interview_deadline, "Interview Date is not created")
        # I check whether final interview meeting is created or not
        evaluations = self.HrEvaluation.search([('employee_id', '=', self.hr_employee.id)])
        self.assertTrue(evaluations.meeting_id, "Meeting is not created")
        # I close this Apprisal by click on "Done" button
        evaluations.button_done_appraisal()
        # I check that state of Evaluation is done.
        self.assertEqual(evaluations.state, 'done', "Evaluation should be in done state")
