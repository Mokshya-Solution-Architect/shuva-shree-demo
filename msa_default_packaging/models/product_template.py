# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_sales_packaging_id = fields.Many2one(
        'uom.uom',
        string='Default Sales Packaging',
        domain="[('id', 'in', uom_ids + uom_id)]",
        help="Default packaging/UoM to use when creating sale orders for this product.",
    )
    default_purchase_packaging_id = fields.Many2one(
        'uom.uom',
        string='Default Purchase Packaging',
        help="Default packaging/UoM to use when creating purchase orders for this product.",
    )
