# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class VariableWeightWizard(models.TransientModel):
    _name = "msa.variable.weight.wizard"
    _description = "Variable Weight Receipt Wizard"

    picking_id = fields.Many2one(
        "stock.picking", string="Receipt",
        required=True, readonly=True, ondelete="cascade")
    line_ids = fields.One2many(
        "msa.variable.weight.wizard.line", "wizard_id",
        string="Weight Lines")
    total_weight = fields.Float(
        string="Total Weight", compute="_compute_total_weight", store=True,
        digits="Product Unit")
    has_errors = fields.Boolean(compute="_compute_has_errors")

    @api.depends("line_ids.weight")
    def _compute_total_weight(self):
        for wizard in self:
            wizard.total_weight = sum(wizard.line_ids.mapped("weight"))

    @api.depends("line_ids.weight")
    def _compute_has_errors(self):
        for wizard in self:
            wizard.has_errors = any(
                float_compare(line.weight, 0, precision_digits=6) <= 0
                for line in wizard.line_ids)

    def _prepare_lines(self):
        self.ensure_one()
        _logger.info("=== _prepare_lines: picking=%s (%s) ===",
                     self.picking_id.name, self.picking_id.id)
        lines = []
        seq = 1
        for move in self.picking_id.move_ids:
            if move.state in ("done", "cancel"):
                _logger.info("  SKIP move %s state=%s", move.id, move.state)
                continue
            product = move.product_id
            if not product.product_tmpl_id.variable_receipt_weight:
                _logger.info("  SKIP %s vrw=False", product.display_name)
                continue
            base_uom = product.uom_id
            move_uom = move.product_uom
            po_line = move.purchase_line_id
            if po_line and po_line.product_qty:
                unit_count = max(1, int(po_line.product_uom_id.round(
                    po_line.product_qty, rounding_method="HALF-UP")))
                _logger.info("  MOVE id=%s product=%s move_uom=%s"
                             " unit_count=%d purchase_line=%s",
                             move.id, product.display_name,
                             move_uom.name, unit_count,
                             po_line.product_qty)
            else:
                if move_uom and move_uom != base_uom:
                    unit_count = max(1, int(move_uom.round(
                        move.product_uom_qty, rounding_method="HALF-UP")))
                else:
                    unit_count = 1
                _logger.info("  MOVE id=%s product=%s move_uom=%s"
                             " unit_count=%d (no PO, derived from move_uom_qty=%s)",
                             move.id, product.display_name,
                             move_uom.name, unit_count, move.product_uom_qty)
            total_kg = move_uom._compute_quantity(
                move.product_uom_qty, base_uom, round=False)
            default_wt = base_uom.round(
                total_kg / unit_count, rounding_method="HALF-UP")
            _logger.info("    move_uom_qty=%s total_kg=%s default_wt=%s",
                         move.product_uom_qty, total_kg, default_wt)
            first_lot = self._generate_first_lot_name(product, consume=False)
            lot_names = self.env["stock.lot"].generate_lot_names(
                first_lot, unit_count) if unit_count > 1 else [
                    {"lot_name": first_lot}]
            for i in range(unit_count):
                ln = lot_names[i]["lot_name"]
                _logger.info("    LINE seq=%d lot=%s wt=%s %s",
                             seq, ln, default_wt, base_uom.name)
                lines.append(Command.create({
                    "product_id": product.id,
                    "move_id": move.id,
                    "sequence": seq,
                    "lot_name": ln,
                    "weight": default_wt,
                    "uom_id": base_uom.id,
                }))
                seq += 1
        if lines:
            self.write({"line_ids": lines})
        _logger.info("  Created %d wizard lines", len(lines))

    def _generate_first_lot_name(self, product, consume=False):
        seq = product.lot_sequence_id
        if seq:
            if consume:
                name = seq.next_by_id()
            else:
                prefix = seq.prefix or ""
                n = seq.number_next_actual
                p = seq.padding
                s = seq.suffix or ""
                name = f"{prefix}{str(n).zfill(p)}{s}"
        else:
            name = self.env["ir.sequence"].next_by_code("stock.lot.serial")
        if not name:
            raise UserError(_("No sequence for '%s'.", product.display_name))
        _logger.info("    lot_sequence: next=%s consume=%s", name, consume)
        return name

    def action_confirm(self):
        self.ensure_one()
        if self.has_errors:
            raise UserError(_("All weights must be positive."))
        picking = self.picking_id
        _logger.info("=== action_confirm: picking=%s (%s) ===",
                     picking.name, picking.id)

        by_move = {}
        for line in self.line_ids:
            by_move.setdefault(
                line.move_id, self.env["msa.variable.weight.wizard.line"])
            by_move[line.move_id] |= line

        all_new_lines = self.env["stock.move.line"]
        for move, wlines in by_move.items():
            product = move.product_id
            base_uom = product.uom_id
            _logger.info("  MOVE id=%s", move.id)
            n_before = len(move.move_line_ids)
            move.move_line_ids.unlink()
            _logger.info("    Unlinked %d lines", n_before)
            ml_vals = []
            total_kg = 0.0
            for wl in wlines.sorted("sequence"):
                lot_name = self._generate_first_lot_name(product, consume=True)
                lot = self.env["stock.lot"].create({
                    "name": lot_name,
                    "product_id": wl.product_id.id,
                    "company_id": picking.company_id.id,
                })
                _logger.info("    LOT=%s wt=%.4f kg", lot.name, wl.weight)
                total_kg += wl.weight
                ml_vals.append({
                    "move_id": move.id,
                    "picking_id": picking.id,
                    "product_id": wl.product_id.id,
                    "product_uom_id": base_uom.id,
                    "quantity": wl.weight,
                    "lot_id": lot.id,
                    "location_id": move.location_id.id,
                    "location_dest_id": move.location_dest_id.id,
                    "picked": True,
                    "company_id": picking.company_id.id,
                })
            rounded_kg = base_uom.round(total_kg, rounding_method="HALF-UP")
            _logger.info("    total=%s kg", rounded_kg)

            move.write({
                "product_uom": base_uom.id,
                "product_uom_qty": rounded_kg,
                "picked": True,
            })

            lines = self.env["stock.move.line"].create(ml_vals)
            _logger.warning(
                "    [VRW] after create: line_ids=%s picking_ids=%s",
                lines.ids,
                lines.mapped("picking_id").ids,
            )
            missing = lines.filtered(lambda ml: not ml.picking_id)
            if missing:
                _logger.warning(
                    "    [VRW] %s lines missing picking_id after create → write",
                    len(missing),
                )
                missing.write({"picking_id": picking.id})
            all_new_lines |= lines
            _logger.info("    Created %d lines with lots", len(lines))

            move.quantity = rounded_kg
            _logger.warning(
                "    [VRW] after move.quantity=%s: via_move=%s picking_ids=%s",
                rounded_kg,
                len(move.move_line_ids),
                move.move_line_ids.mapped("picking_id").ids,
            )

        _logger.info("  Calling _action_done on %d move lines...", len(all_new_lines))
        all_new_lines._action_done()
        _logger.warning(
            "  [VRW] after _action_done: line_ids=%s picking_ids=%s",
            all_new_lines.ids,
            all_new_lines.mapped("picking_id").ids,
        )

        for move in picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel")):
            move.write({"state": "done", "date": fields.Datetime.now()})
        picking.write({"state": "done", "date_done": fields.Datetime.now()})

        picking._msa_force_link_move_lines()
        _logger.warning(
            "  [VRW] confirm done: picking.move_line_ids=%s via_move=%s",
            len(picking.move_line_ids),
            len(picking.move_ids.move_line_ids),
        )
        return {"type": "ir.actions.act_window_close"}

    def action_cancel(self):
        return {"type": "ir.actions.act_window_close"}


class VariableWeightWizardLine(models.TransientModel):
    _name = "msa.variable.weight.wizard.line"
    _description = "Variable Weight Receipt Wizard Line"
    _order = "sequence, id"

    wizard_id = fields.Many2one(
        "msa.variable.weight.wizard", string="Wizard",
        required=True, readonly=True, ondelete="cascade")
    move_id = fields.Many2one(
        "stock.move", string="Stock Move",
        required=True, readonly=True, ondelete="cascade")
    product_id = fields.Many2one(
        "product.product", string="Product",
        required=True, readonly=True)
    sequence = fields.Integer(string="Unit #", required=True)
    lot_name = fields.Char(string="Lot / Barcode", required=True)
    weight = fields.Float(
        string="Actual Weight", required=True, digits="Product Unit")
    uom_id = fields.Many2one(
        "uom.uom", string="Unit", required=True, readonly=True)

    @api.constrains("weight")
    def _check_weight_positive(self):
        for line in self:
            if float_compare(line.weight, 0, precision_digits=6) <= 0:
                raise UserError(_(
                    "Weight for unit #%d (%s) must be positive.",
                    line.sequence, line.lot_name))
