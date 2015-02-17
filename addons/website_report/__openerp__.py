# -*- coding: utf-8 -*-
{
    'name': 'Website Report',
    'category': 'Website',
    'summary': 'Website Editor on reports',
    'version': '1.0',
    'description': """
Use the website editor to customize your reports.
        """,
    'author': 'Odoo SA',
    'depends': ['base', 'website', 'report'],
    'data': [
        'views/layouts.xml',
    ],
    'installable': True,
    'auto_install': True,
}
