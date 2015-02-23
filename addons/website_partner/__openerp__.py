# -*- coding: utf-8 -*-
{
    'name': 'Website Partner',
    'category': 'Website',
    'summary': 'Partner Module for Website',
    'version': '0.1',
    'description': """Base module holding website-related stuff for partner model""",
    'author': 'Odoo SA',
    'depends': ['website'],
    'data': [
        'views/res_partner_view.xml',
        'views/website_partner_view.xml',
        'data/website_data.xml',
    ],
    'demo': ['data/demo.xml'],
    'qweb': [
    ],
    'installable': True,
}
