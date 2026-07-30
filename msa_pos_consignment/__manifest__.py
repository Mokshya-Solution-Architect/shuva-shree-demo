# -*- coding: utf-8 -*-
{
    'name': 'SS POS Consignment Dispatch',
    'version': '19.0.1.2.1',
    'category': 'Sales/Point of Sale',
    'summary': 'Consignment dispatch and settlement workflow for POS',
    'description': """
        Adds a two-phase consignment / route-sales workflow to Odoo POS.

        Phase 1 — Dispatch:
            Supplier-distributor comes to the warehouse and takes products.
            Stock moves immediately to a Consignment Transit location.
            No payment is required at this stage.

        Phase 2 — Settlement (next day):
            Supplier returns and reports how many products were sold.
            - Sold qty      → POS order created; payment collected from cashier.
            - Good returns  → stock moves back to warehouse.
            - Damaged/scrap → routed via msa_pos_exchange scrap / rework locations.
    """,
    'author': 'Mokshya Solution Architect Pvt. Ltd.',
    'website': 'https://www.mokshyasolution.com',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'stock', 'msa_pos_uom', 'msa_pos_exchange'],
    'data': [
        'security/ir.model.access.csv',
        'security/pos_consignment_security.xml',
        'data/ir_sequence_data.xml',
        'data/stock_locations_data.xml',
        'views/pos_config_views.xml',
        'views/res_config_settings_views.xml',
        'views/pos_consignment_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'msa_pos_consignment/static/src/**/*',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
