# -*- coding: utf-8 -*-
# Part of MSA Solutions. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        Move = self.env["stock.move"]
        for vals in vals_list:
            if vals.get("move_id") and not vals.get("picking_id"):
                move = Move.browse(vals["move_id"])
                if move.picking_id:
                    vals["picking_id"] = move.picking_id.id
        lines = super().create(vals_list)
        # Defend against native paths that drop picking_id during create.
        orphans = lines.filtered(lambda ml: ml.move_id.picking_id and not ml.picking_id)
        if orphans:
            for ml in orphans:
                ml.picking_id = ml.move_id.picking_id
            _logger.warning(
                "[VRW] stock.move.line.create repaired picking_id on %s lines: %s",
                len(orphans),
                orphans.ids,
            )
        return lines
