# -*- coding: utf-8 -*-

{
    'name': 'IBAN Bank Accounts',
    'version': '1.0',
    'category': 'Hidden/Dependency',
    'description': """
This module installs the base for IBAN (International Bank Account Number) bank accounts and checks for it's validity.
======================================================================================================================

The ability to extract the correctly represented local accounts from IBAN accounts
with a single statement.
    """,
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com',
    'depends': ['base'],
    'data': [
        'data/base_iban_data.xml',
    ],
    'installable': True,
}
