{
    'name': 'Web Editor',
    'category': 'Hidden',
    'description': """
OpenERP Web Editor widget.
==========================

""",
    'author': 'Odoo',
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'views/editor.xml',
        'views/iframe.xml',
        'views/snippets.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'auto_install': True
}
