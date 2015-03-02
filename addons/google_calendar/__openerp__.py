# -*- coding: utf-8 -*-


{
    'name': 'Google Calendar',
    'version': '1.0',
    'category': 'Tools',
    'description': """
The module adds the possibility to synchronize Google Calendar with Odoo
========================================================================
""",
    'author': 'Odoo SA',
    'website': 'https://www.odoo.com/page/crm',
    'depends': ['google_account', 'calendar'],
    'qweb': ['static/src/xml/*.xml'],
    'data': [
        'views/res_config_view.xml',
        'security/ir.model.access.csv',
        'views/google_calendar.xml',
        'views/res_users.xml',
        'data/google_calendar.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
