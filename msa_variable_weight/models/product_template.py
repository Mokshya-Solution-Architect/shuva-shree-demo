# -*- coding: utf-8 -*-
# Part of MSA Solutions. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    variable_receipt_weight = fields.Boolean(
        string='Variable Receipt Weight',
        default=False,
        help=(
            "Enable this if the product's purchase unit (e.g., Bora, Sack, Crate) "
            "has a variable weight that differs per physical unit.\n"
            "During stock receipt, a wizard will prompt the operator to enter the "
            "actual weight for each physical unit received. The system will "
            "automatically generate a unique lot (barcode) per unit with its "
            "actual weight."
        ),
    )
