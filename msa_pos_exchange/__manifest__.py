# -*- coding: utf-8 -*-
{
    'name': 'SS POS Product Exchange',
    'version': '19.0.1.1.0',
    'category': 'Sales/Point of Sale',
    'summary': 'No-refund POS exchanges with scrap / rework routing',
    'description': """
        Cashiers exchange returned goods at the POS counter without cash refund.

        - Expired → scrap location
        - Packaging damage → rework (reusable) + scrap (waste)
        - Replacement always issued from sellable Finished Goods
        - Zero-amount POS order for session audit (no cash movement)
    """,
    'author': 'Mokshya Solution Architect Pvt. Ltd.',
    'website': 'https://www.mokshyasolution.com',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/pos_exchange_security.xml',
        'data/ir_sequence_data.xml',
        'data/stock_locations_data.xml',
        'views/pos_config_views.xml',
        'views/res_config_settings_views.xml',
        'views/pos_exchange_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'msa_pos_exchange/static/src/**/*',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
