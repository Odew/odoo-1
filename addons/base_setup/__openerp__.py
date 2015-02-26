# -*- coding: utf-8 -*-

{
    'name': 'Initial Setup Tools',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
This module helps to configure the system at the installation of a new database.
================================================================================

Shows you a list of applications features to install from.

    """,
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com',
    'depends': ['base', 'web_kanban'],
    'data': [
        'views/base_setup_views.xml',
        'views/res_config_view.xml',
        'views/res_partner_view.xml',
        'views/base_setup.xml',
    ],
    'demo': [],
    'installable': True,
}
