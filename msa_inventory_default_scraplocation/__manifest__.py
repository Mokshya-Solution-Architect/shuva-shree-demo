{
    'name': "Auto Scrap Location",
    'version': '19.0.0.0',
    'category': 'Inventory',
    'summary': "Automatically sets default scrap location for stock scraps",
    'description': """
This module automatically assigns a default scrap location
when creating scrap orders in Inventory.

Features:
- Auto-fills Scrap Location field
- Uses predefined 'Scrap Location'
""",
    'author': 'DFW IT Partner',
    'website': 'https://www.dfwitpartner.com',
    'depends': ['base','stock'],
    'data': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}