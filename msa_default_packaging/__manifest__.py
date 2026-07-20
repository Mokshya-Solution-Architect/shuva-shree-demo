# -*- coding: utf-8 -*-
{
    'name': 'SS Default Packaging',
    'version': '19.0.1.0.0',
    'category': 'Sales/Purchase',
    'summary': 'Set default packaging/UoM per product for sales and purchase orders',
    'description': """
        Adds two fields on product.template:
        - Default Sales Packaging (in the Sales tab)
        - Default Purchase Packaging (in the Purchase tab)

        When creating a sale or purchase order, the selected product's
        default packaging is auto-selected as the line's UoM.
    """,
    'author': 'Mokshya Solution Architect Pvt. Ltd.',
    'website': 'https://www.mokshyasolution.com',
    'license': 'LGPL-3',
    'depends': ['product', 'sale', 'purchase'],
    'data': [
        'views/product_template_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
