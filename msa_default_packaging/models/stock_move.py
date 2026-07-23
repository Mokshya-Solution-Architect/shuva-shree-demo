from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.depends(
        'product_id',
        'product_id.uom_id',
        'product_id.uom_ids',
        'product_id.seller_ids',
        'product_id.seller_ids.product_uom_id',
        'product_id.product_tmpl_id.purchase_default_packaging_id',
        'product_id.product_tmpl_id.sales_default_packaging_id',
    )
    def _compute_allowed_uom_ids(self):
        super()._compute_allowed_uom_ids()
        for move in self:
            tmpl = move.product_id.product_tmpl_id
            if tmpl.purchase_default_packaging_id:
                move.allowed_uom_ids |= tmpl.purchase_default_packaging_id
            if tmpl.sales_default_packaging_id:
                move.allowed_uom_ids |= tmpl.sales_default_packaging_id

    @api.depends('product_id', 'picking_type_id')
    def _compute_product_uom(self):
        super()._compute_product_uom()
        for move in self:
            if not move.product_id or not move.picking_type_id:
                continue
            tmpl = move.product_id.product_tmpl_id
            code = move.picking_type_id.code
            if code == 'incoming':
                default_uom = tmpl.purchase_default_packaging_id
            elif code == 'outgoing':
                default_uom = tmpl._get_default_sales_uom()
            else:
                continue
            if default_uom and default_uom != move.product_id.uom_id:
                move.product_uom = default_uom


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.depends(
        'product_id',
        'product_id.uom_id',
        'product_id.uom_ids',
        'product_id.seller_ids',
        'product_id.seller_ids.product_uom_id',
        'product_id.product_tmpl_id.purchase_default_packaging_id',
        'product_id.product_tmpl_id.sales_default_packaging_id',
    )
    def _compute_allowed_uom_ids(self):
        super()._compute_allowed_uom_ids()
        for line in self:
            tmpl = line.product_id.product_tmpl_id
            if tmpl.purchase_default_packaging_id:
                line.allowed_uom_ids |= tmpl.purchase_default_packaging_id
            if tmpl.sales_default_packaging_id:
                line.allowed_uom_ids |= tmpl.sales_default_packaging_id
