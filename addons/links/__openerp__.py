{
    'name': 'Link Tracker',
    'category': 'Hidden',
    'description': """
Create short and trackable URLs.
=====================================================
        """,
    'version': '1.0',
    'depends':['marketing', 'utm'],
    'data' : [
        'views/links.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'auto_install': False,
}