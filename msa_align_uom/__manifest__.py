{
    'name': "Align UOM in Barcode, Picking and Pick Slip",
    'version': '19.0.0.0',
    'category': 'Inventory',
    'summary': "Aligns the UOM from confirmed Sales Orders and Purchase Orders across warehouse operations",
    'description': """
    Features:
    - Aligns the Unit of Measure (UOM) from confirmed Sales Orders and Purchase Orders
    - Displays the same UOM in the Barcode App
    - Displays the same UOM in Inventory Pickings
    - Displays the same UOM on Pick Slip reports
    - Reduces confusion caused by automatic UOM conversions during picking and delivery
    """,
    'author': 'Mokshya Solution Architect Pvt. Ltd.',
    'website': 'https://www.mokshyasolution.com',
    'depends': ['base','stock','sale_management','purchase','barcodes'],
    'data': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

