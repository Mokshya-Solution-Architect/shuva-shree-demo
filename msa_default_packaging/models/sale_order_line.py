# -*- coding: utf-8 -*-

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id.product_tmpl_id.default_sales_packaging_id')
    def _compute_allowed_uom_ids(self):
        super()._compute_allowed_uom_ids()
        for line in self:
            if line.product_id:
                default_pkg = line.product_id.product_tmpl_id.default_sales_packaging_id
                if default_pkg:
                    line.allowed_uom_ids |= default_pkg

    @api.depends('product_id',
                 'product_id.product_tmpl_id.default_sales_packaging_id')
    def _compute_product_uom_id(self):
        super()._compute_product_uom_id()
        for line in self:
            if line.product_id:
                default_pkg = line.product_id.product_tmpl_id.default_sales_packaging_id
                if default_pkg:
                    line.product_uom_id = default_pkg
