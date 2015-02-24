{
    'name': 'Link Tracker Frontend',
    'category': 'Hidden',
    'description': """
A frontend interface to create short and trackable URLs.
=====================================================
        """,
    'version': '1.0',
    'depends':['links', 'website'],
    'data' : [
        'views/website_links_template.xml',
        'views/website_links_graphs.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'auto_install': True,
}
