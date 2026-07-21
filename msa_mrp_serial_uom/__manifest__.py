{
    'name': "MRP Serial Number by Alternate UOM",
    'version': '19.0.1.1.0',
    'category': 'Manufacturing',
    'summary': "Generate one lot per alternate UOM unit on manufacturing orders",
    'description': """
    When manufacturing in an alternate UOM (e.g. 50 Jhola where 1 Jhola = 6 Pcs):

    - Use product tracking "By Lots" (serials cannot hold 6 Pcs each).
    - Click Generate Lots → Generate → Apply to create 50 unique lots (one per Jhola).
    - Produce All stocks each lot with 1 Jhola (= 6 Pcs).

    Serial + packaging UOM is blocked: Odoo requires each serial to hold at most 1.0 base UOM.
    """,
    'author': 'Mokshya Solution Architect Pvt. Ltd.',
    'website': 'https://www.mokshyasolution.com',
    'depends': ['mrp'],
    'data': [
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
