# -*- coding: utf-8 -*-
# Part of MSA Solutions. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    received_base_uom_qty = fields.Float(
        string="Rec. Base UoM",
        digits="Product Unit",
        compute="_compute_received_base_uom_qty",
        store=True,
        help="Received quantity in the product's base unit of measure "
             "(e.g., kg, litres). Computed from done stock moves.",
    )

    @api.depends("move_ids.state", "move_ids.quantity",
                 "move_ids.product_uom", "product_id", "product_id.uom_id")
    def _compute_received_base_uom_qty(self):
        for line in self:
            if not line.product_id:
                line.received_base_uom_qty = 0.0
                continue
            base_uom = line.product_id.uom_id
            total = 0.0
            for move in line.move_ids.filtered(
                lambda m: m.state == "done"
                and m.picking_code == "incoming"
            ):
                total += move.product_uom._compute_quantity(
                    move.quantity, base_uom, round=False)
            line.received_base_uom_qty = base_uom.round(
                total, rounding_method="HALF-UP")

    def _msa_is_variable_weight(self):
        self.ensure_one()
        return bool(self.product_id.product_tmpl_id.variable_receipt_weight)

    def _msa_packaging_qty_from_move(self, move):
        """Count physical purchase units on a VRW move (1 done move line = 1 unit)."""
        return sum(
            1 for ml in move.move_line_ids
            if ml.product_uom_id.compare(ml.quantity, 0.0) > 0
        )

    def _msa_move_qty_in_po_uom(self, move, qty_to_compute):
        """Convert move qty to PO line UoM, or count packaging units for done VRW moves."""
        self.ensure_one()
        if self._msa_is_variable_weight() and move.state == "done":
            return float(self._msa_packaging_qty_from_move(move))
        return move.product_uom._compute_quantity(
            qty_to_compute, self.product_uom_id, rounding_method="HALF-UP")

    @api.depends(
        "move_ids.move_line_ids.quantity",
        "move_ids.move_line_ids.product_uom_id",
        "product_id.product_tmpl_id.variable_receipt_weight",
    )
    def _compute_qty_received(self):
        # Extra depends so VRW line-count changes trigger recompute.
        super()._compute_qty_received()

    def _prepare_qty_received(self):
        received_qties = super()._prepare_qty_received()
        for line in self:
            if not line.product_id or not line._msa_is_variable_weight():
                continue
            if line.qty_received_method != "stock_moves":
                continue
            total = 0.0
            for move in line._get_po_line_moves():
                if move.state != "done":
                    continue
                packaging_qty = line._msa_packaging_qty_from_move(move)
                if move._is_purchase_return():
                    if not move.origin_returned_move_id or move.to_refund:
                        total -= packaging_qty
                elif (
                    move.origin_returned_move_id
                    and move.origin_returned_move_id._is_dropshipped()
                    and not move._is_dropshipped_returned()
                ):
                    # Dropship returned to stock (not supplier): do not double-count.
                    pass
                elif (
                    move.origin_returned_move_id
                    and move.origin_returned_move_id._is_purchase_return()
                    and not move.to_refund
                ):
                    pass
                else:
                    total += packaging_qty
            line._track_qty_received(total)
            received_qties[line] = total
        return received_qties

    def _get_qty_procurement(self):
        self.ensure_one()
        if not self._msa_is_variable_weight():
            return super()._get_qty_procurement()
        qty = 0.0
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
        for move in outgoing_moves:
            qty_to_compute = (
                move.quantity if move.state == "done" else move.product_uom_qty)
            qty -= self._msa_move_qty_in_po_uom(move, qty_to_compute)
        for move in incoming_moves:
            qty_to_compute = (
                move.quantity if move.state == "done" else move.product_uom_qty)
            qty += self._msa_move_qty_in_po_uom(move, qty_to_compute)
        return qty
