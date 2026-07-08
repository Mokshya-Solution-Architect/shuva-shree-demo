from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = ['purchase.order.line', 'shuva.alt.unit.mixin']

    shuva_avg_qty_per_pack = fields.Float(string="Average Qty per Pack")
    shuva_estimated_qty = fields.Float(string="Estimated Qty", readonly=True)
    shuva_actual_received_qty = fields.Float(string="Actual Received Qty", readonly=True)

    @api.onchange('product_id')
    def _onchange_shuva_product_id(self):
        for line in self:
            product = line.product_id
            if not product:
                continue

            tmpl = product.product_tmpl_id

            if tmpl.shuva_default_pack_type_id:
                line.shuva_pack_type_id = tmpl.shuva_default_pack_type_id

            if tmpl.shuva_average_qty_per_pack:
                line.shuva_avg_qty_per_pack = tmpl.shuva_average_qty_per_pack
            elif tmpl.shuva_default_pack_qty:
                line.shuva_avg_qty_per_pack = tmpl.shuva_default_pack_qty
            elif line.shuva_pack_type_id:
                pack = line.shuva_pack_type_id
                line.shuva_avg_qty_per_pack = (
                    pack.average_qty_per_pack
                    if pack.is_variable_qty
                    else pack.fixed_qty_per_pack
                )

    @api.onchange('shuva_pack_type_id')
    def _onchange_shuva_pack_type_id(self):
        for line in self:
            pack = line.shuva_pack_type_id
            if not pack:
                continue

            line.shuva_avg_qty_per_pack = (
                pack.average_qty_per_pack
                if pack.is_variable_qty
                else pack.fixed_qty_per_pack
            )

    @api.onchange('shuva_alt_qty', 'shuva_avg_qty_per_pack')
    def _onchange_shuva_alt_qty_compute_qty(self):
        for line in self:
            if line.shuva_alt_qty and line.shuva_avg_qty_per_pack:
                qty = line.shuva_alt_qty * line.shuva_avg_qty_per_pack
                line.product_qty = qty
                line.shuva_estimated_qty = qty


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super().button_confirm()

        for order in self:
            for picking in order.picking_ids:
                for move in picking.move_ids:
                    po_line = move.purchase_line_id
                    if not po_line:
                        continue

                    move.shuva_alt_qty = po_line.shuva_alt_qty
                    move.shuva_pack_type_id = po_line.shuva_pack_type_id.id
                    move.shuva_pack_note = po_line.shuva_pack_note
                    move.shuva_avg_qty_per_pack = po_line.shuva_avg_qty_per_pack
                    move.shuva_estimated_qty = po_line.shuva_estimated_qty

        return res