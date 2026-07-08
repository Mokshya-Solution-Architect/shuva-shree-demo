{
    'name': 'Shuva Food Custom Workflows',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Alt-unit packs, unique pack barcodes, MRP jumbo packs, returns routing, and reports for food manufacturing.',
    'author': 'Mokshya Solution Architect Pvt. ltd.',
    'license': 'LGPL-3',
    'depends': [
        'stock', 'purchase', 'sale_management', 'mrp', 'point_of_sale', 'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/pack_type_views.xml',
        'views/product_views.xml',
        'views/purchase_views.xml',
        'views/sale_views.xml',
        'views/stock_lot_views.xml',
        'views/stock_picking_views.xml',
        'views/mrp_views.xml',
        'views/return_reason_views.xml',
        'views/report_views.xml',
        'wizards/pack_lot_wizard_views.xml',
        'wizards/mrp_finished_pack_wizard_views.xml',
    ],
    # 'assets': {
    #     'point_of_sale._assets_pos': [
    #         'shuva_food_custom/static/src/js/pos_lot_barcode.js',
    #     ],
    # },
    'installable': True,
    'application': False,
}
