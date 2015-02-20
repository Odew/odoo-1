# -*- coding: utf-8 -*-

{
    'name': 'OAuth2 Authentication',
    'version': '1.0',
    'category': 'Tools',
    'description': """
Allow users to login through OAuth2 Provider.
=============================================
""",
    'author': 'Odoo SA',
    'maintainer': 'Odoo SA',
    'website': 'https://www.odoo.com',
    'depends': ['base', 'web', 'base_setup', 'auth_signup'],
    'data': [
        'data/auth_oauth_data.xml',
        'security/ir.model.access.csv',
        'views/auth_oauth_login.xml',
        'views/auth_oauth_view.xml',
        'views/res_config.xml',
        'views/res_users.xml',
    ],
    'test': [
        'test/auth_oauth_data.yml',
    ],
    'installable': True,
}
