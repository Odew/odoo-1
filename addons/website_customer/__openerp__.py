# -*- coding: utf-8 -*-
{
    'name': 'Customer References',
    'category': 'Website',
    'website': 'https://www.odoo.com/page/website-builder',
    'summary': 'Publish Your Customer References',
    'version': '1.0',
    'description': """
Odoo Customer References
===========================
""",
    'author': 'Odoo SA',
    'depends': [
        'crm_partner_assign',
        'website_partner',
        'website_google_map',
    ],
    'demo': [
        'data/website_customer_demo.xml',
    ],
    'data': [
        'views/website_customer.xml',
        'views/website_customer_view.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
    'qweb': [],
    'installable': True,
}
