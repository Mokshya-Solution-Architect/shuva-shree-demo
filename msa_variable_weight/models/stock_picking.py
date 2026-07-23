# -*- coding: utf-8 -*-

import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_detailed_operations(self):
        self.ensure_one()
        action = super().action_detailed_operations()
        action["domain"] = [
            "|",
            ("picking_id", "=", self.id),
            ("move_id.picking_id", "=", self.id),
        ]
        _logger.warning(
            "[VRW] detailed ops for %s domain=%s (native move_line_ids=%s via_move=%s)",
            self.name,
            action["domain"],
            len(self.move_line_ids),
            len(self.move_ids.move_line_ids),
        )
        return action

    def _msa_force_link_move_lines(self):
        self.ensure_one()
        self.env.cr.execute(
            """
            UPDATE stock_move_line AS sml
               SET picking_id = %s
              FROM stock_move AS sm
             WHERE sml.move_id = sm.id
               AND sm.picking_id = %s
               AND (sml.picking_id IS NULL OR sml.picking_id != %s)
            """,
            (self.id, self.id, self.id),
        )
        updated = self.env.cr.rowcount
        self.env["stock.move.line"].invalidate_model(["picking_id"])
        self.invalidate_recordset(["move_line_ids"])
        _logger.warning(
            "[VRW] force-link picking=%s (%s): updated %s move lines; "
            "now move_line_ids=%s via_move=%s",
            self.name,
            self.id,
            updated,
            len(self.move_line_ids),
            len(self.move_ids.move_line_ids),
        )
        return updated

    def _pre_action_done_hook(self):
        if self.env.context.get("skip_variable_weight"):
            return super()._pre_action_done_hook()

        incoming = self.filtered(
            lambda p: p.picking_type_id.code == "incoming")
        if not incoming:
            return super()._pre_action_done_hook()

        wizard_needed = False
        for picking in incoming:
            for move in picking.move_ids:
                if move.state in ("done", "cancel"):
                    continue
                if not move.product_id.product_tmpl_id.variable_receipt_weight:
                    continue
                lines = move.move_line_ids.filtered(
                    lambda ml: ml.product_uom_id.compare(
                        ml.quantity, 0) > 0)
                if lines and all(ml.lot_id for ml in lines):
                    _logger.info(
                        "[PICKING] %s move=%s: already has lots, skip wizard",
                        picking.name, move.id)
                    continue
                wizard_needed = True

        if not wizard_needed:
            return super()._pre_action_done_hook()

        picking = incoming[0]
        _logger.info("[PICKING] Launching wizard for %s", picking.name)
        return picking._action_launch_variable_weight_wizard()

    def _action_launch_variable_weight_wizard(self):
        self.ensure_one()
        wizard = self.env["msa.variable.weight.wizard"].create({
            "picking_id": self.id})
        wizard._prepare_lines()
        view = self.env.ref(
            "msa_variable_weight.view_variable_weight_wizard_form")
        return {
            "name": _("Record Variable Weights"),
            "type": "ir.actions.act_window",
            "res_model": "msa.variable.weight.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "views": [(view.id, "form")],
            "target": "new",
            "context": self.env.context,
        }
