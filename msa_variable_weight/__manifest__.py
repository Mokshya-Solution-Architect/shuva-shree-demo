# -*- coding: utf-8 -*-
# Part of MSA Solutions. See LICENSE file for full copyright and licensing details.

{
    'name': 'MSA Variable Weight Receipt',
    'version': '19.0.1.1.2',
    'category': 'Inventory/Purchase',
    'summary': 'Handle variable-weight purchase receipts with per-unit lot/barcode generation',
    'description': """
        When purchasing products that come in variable-weight packaging units
        (e.g., a "Bora" of potatoes weighing 45-55 kg), this module provides
        a guided wizard during stock receipt validation.

        For each physical unit received, the operator enters the actual weight.
        The system automatically:
        - Generates a unique stock lot (barcode) per physical unit
        - Creates individual stock move lines with actual weights
        - Sets the total received quantity to the sum of all unit weights
        - Links move lines to the receipt (so Detailed Operations / Lot labels work)

        This is essential for industries where raw material quality varies
        and purchase units do not have fixed conversion ratios.
    """,
    'author': 'Mokshya Solution Architect Pvt. Ltd.',
    'website': 'https://www.mokshyasolution.com',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'purchase',
        'purchase_stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/purchase_order_line_views.xml',
        'wizard/variable_weight_receipt_views.xml',
    ],
    'post_init_hook': '_post_init_link_vrw_move_lines',
    'assets': {},
    'installable': True,
    'auto_install': False,
    'application': False,
}
