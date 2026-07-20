# -*- coding: utf-8 -*-

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_id.product_tmpl_id.default_purchase_packaging_id')
    def _compute_allowed_uom_ids(self):
        super()._compute_allowed_uom_ids()
        for line in self:
            if line.product_id:
                default_pkg = line.product_id.product_tmpl_id.default_purchase_packaging_id
                if default_pkg:
                    line.allowed_uom_ids |= default_pkg

    @api.onchange('product_id')
    def onchange_product_id(self):
        super().onchange_product_id()
        if self.product_id:
            default_pkg = self.product_id.product_tmpl_id.default_purchase_packaging_id
            if default_pkg:
                self.product_uom_id = default_pkg
