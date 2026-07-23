# -*- coding: utf-8 -*-
{
    "name": "MSA Default Packaging",
    "summary": "Default sales/purchase packaging from product UoMs",
    "description": "Adds default Sales and Purchase packaging on products and auto-fills SO/PO line unit.",
    "author": "Mokshya Solution Architect Pvt. Ltd.",
    "website": "https://www.mokshyasolution.com",
    "category": "Customization",
    "version": "19.0.0.1",
    "depends": [
        "base",
        "product",
        "sale_management",
        "purchase",
        "stock",
        "website_sale",
    ],
    "data": [
        "views/default_package_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}