# -*- coding: utf-8 -*-
{
    'name': 'SS Lot/SN Sticker Label (PDF)',
    'version': '19.0.1.7.2',
    'category': 'Inventory/Inventory',
    'summary': 'Print sleek PDF lot/serial labels as one barcode per sticker page',
    'description': """
        Keeps the native Lot/SN PDF label look (product code, name, SN, barcode,
        expiry lines) but prints one label per page on a 50x25mm sticker
        instead of the A4 4x12 sheet.

        Adds a highlighted Lot/SN Labels header button and a barcode smart
        button on transfers with lot/serial-tracked products.
    """,
    'author': 'Mokshya Solution Architect Pvt. Ltd.',
    'website': 'https://www.mokshyasolution.com',
    'license': 'LGPL-3',
    'depends': ['stock', 'product_expiry'],
    'data': [
        'report/paperformat.xml',
        'report/report_lot_label.xml',
        'views/stock_picking_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'msa_lot_label_sticker/static/src/scss/lot_label_sticker.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
