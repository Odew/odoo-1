# -*- coding: utf-8 -*-
{
    'name': 'Employee Evaluations',
    'version': '1.0',
    'author': 'Odoo S.A',
    'category': 'Human Resources',
    'sequence': 31,
    'website': 'https://www.odoo.com',
    'summary': 'Periodical Evaluations',
    'images': ['images/hr_evaluation_analysis.jpeg',
               'images/hr_evaluation.jpeg',
               'images/hr_interview_requests.jpeg'],
    'depends': ['hr', 'calendar', 'survey'],
    'description': """
Periodical Employees evaluation
==============================================

By using this application you can maintain the motivational process by doing periodical evaluations of your employees' performance. The regular assessment of human resources can benefit your people as well your organization.

An evaluation plan can be assigned to each employee. These plans define the frequency and the way you manage your periodic personal evaluations.

Key Features
------------
* Ability to create employees evaluations.
* An evaluation can be created by an employee's manager or automatically based on schedule which defined in employee form.
* The evaluation is done according to a plan in which various surveys can be created. Each survey can be answered by a particular level in the employees hierarchy. The final review and evaluation is done by the manager.
* Manager, colleague, collaborator, and self receives automatic email to perform a periodical evaluation when appraisal is started.
* Every evaluation/Appraisal Form filled by employees, colleague, collaborator, can be viewed in a PDF form.
* Meeting Requests are created manually according to employees evaluation plans.
""",
    "data": [
        'security/ir.model.access.csv',
        'security/hr_evaluation_security.xml',
        'views/hr_evaluation_view.xml',
        'report/hr_evaluation_report_view.xml',
        'data/survey_data_appraisal.xml',
        'data/hr_evaluation_data.xml',
        'views/hr_evaluation.xml',
    ],
    "demo": ["data/hr_evaluation_demo.xml"],
    'installable': True,
    'application': True,
}
