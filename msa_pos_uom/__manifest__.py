# -*- coding: utf-8 -*-
{
    'name': 'MSA POS UoM Selector',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Sell in packaging UoMs (Dozen, Jhola, Jumbo…) directly from the POS',
    'description': """
        Adds a Unit of Measure selector to POS order lines.
        Cashiers can choose from the product's base UoM plus any Packagings
        defined on the product.  price_unit and qty are stored in the
        selected UoM; stock moves, procurement, and invoices all receive
        the correct UoM for downstream conversion.
    """,
    'author': 'Mokshya Solution Architect Pvt. Ltd.',
    'website': 'https://www.mokshyasolution.com',
    'license': 'LGPL-3',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'msa_pos_uom/static/src/js/msa_pos_uom.js',
            'msa_pos_uom/static/src/js/UomSelectorButton.js',
            'msa_pos_uom/static/src/xml/UomSelectorButton.xml',
            'msa_pos_uom/static/src/xml/msa_pos_uom_orderline.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
