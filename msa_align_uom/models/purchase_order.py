from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _purchase_line_move_uom_pair(self, qty_in_line_uom):
        """Use PO line UOM on receipt moves when it shares a reference with product UOM (SO parity)."""
        self.ensure_one()
        line_uom = self.product_uom_id
        ref_uom = self.product_id.uom_id
        if not line_uom or not ref_uom:
            return line_uom._adjust_uom_quantities(qty_in_line_uom, ref_uom)
        if line_uom == ref_uom:
            return qty_in_line_uom, line_uom
        if not line_uom._has_common_reference(ref_uom):
            return line_uom._adjust_uom_quantities(qty_in_line_uom, ref_uom)
        return line_uom.round(qty_in_line_uom), line_uom

    def _prepare_stock_moves(self, picking):
        """Receipt moves express demand in ``product_uom_id`` (POL) instead of folding to ``product.uom_id``."""
        self.ensure_one()
        res = []
        if self.product_id.type != 'consu':
            return res

        price_unit = self._get_stock_move_price_unit()
        qty = self._get_qty_procurement()

        move_dests = self.move_dest_ids or self.move_ids.move_dest_ids
        move_dests = move_dests.filtered(
            lambda m: m.state != 'cancel' and not m._is_purchase_return()
        )

        if not move_dests:
            qty_to_attach = 0
            qty_to_push = self.product_qty - qty
        else:
            move_dests_initial_demand = self._get_move_dests_initial_demand(move_dests)
            qty_to_attach = move_dests_initial_demand - qty
            qty_to_push = self.product_qty - move_dests_initial_demand

        if self.product_uom_id.compare(qty_to_attach, 0.0) > 0:
            product_uom_qty, product_uom = self._purchase_line_move_uom_pair(qty_to_attach)
            res.append(self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom))
        if not self.product_uom_id.is_zero(qty_to_push):
            product_uom_qty, product_uom = self._purchase_line_move_uom_pair(qty_to_push)
            extra_move_vals = self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
            extra_move_vals['move_dest_ids'] = False
            res.append(extra_move_vals)
        return res
