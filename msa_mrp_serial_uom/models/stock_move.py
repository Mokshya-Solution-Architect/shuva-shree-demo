import logging

from odoo import models
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _msa_is_alt_uom_finished_move(self):
        """Finished move on an MO whose quantity is expressed in an alternate UOM."""
        self.ensure_one()
        production = self.production_id
        return bool(
            production
            and production.product_tracking == 'lot'
            and self.product_id == production.product_id
            and production._msa_is_alt_uom_mo()
        )

    def _msa_uses_packaging_tracked_uom(self):
        self.ensure_one()
        if self._msa_is_alt_uom_finished_move():
            return True
        return (
            self.product_id.tracking in ('serial', 'lot')
            and self.product_uom
            and self.product_uom != self.product_id.uom_id
        )

    def _get_packaging_sml_uom_and_qty(self):
        self.ensure_one()
        base_uom = self.product_id.uom_id
        if self._msa_is_alt_uom_finished_move():
            return base_uom.id, self.production_id._msa_alt_uom_factor()
        if self._msa_uses_packaging_tracked_uom():
            return base_uom.id, self.product_uom._compute_quantity(1.0, base_uom)
        if self.product_id.tracking == 'serial':
            return base_uom.id, 1.0
        return self.product_uom.id, self.quantity

    def _msa_alt_uom_line_count(self, qty):
        self.ensure_one()
        if self.production_id.lot_producing_ids:
            return len(self.production_id.lot_producing_ids)
        production = self.production_id
        if production and production._msa_is_alt_uom_mo():
            return int(production.product_uom_id.round(qty, rounding_method='HALF-UP'))
        return int(self.product_uom.round(qty, rounding_method='HALF-UP'))

    def _msa_lines_match_alt_uom_lots(self):
        self.ensure_one()
        if not self._msa_is_alt_uom_finished_move():
            return False
        production = self.production_id
        lots = production.lot_producing_ids
        if not lots:
            return False
        factor = production._msa_alt_uom_factor()
        lines = self.move_line_ids
        return (
            len(lines) == len(lots)
            and len(lines.lot_id) == len(lots)
            and all(
                production.product_id.uom_id.compare(line.quantity_product_uom, factor) == 0
                for line in lines
            )
        )

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(quantity, reserved_quant)
        if (
            self._msa_is_alt_uom_finished_move()
            and len(self.production_id.lot_producing_ids) > 1
        ):
            vals.pop('lot_id', None)
        return vals

    def _set_lot_ids(self):
        alt_finished = self.filtered(
            lambda m: m._msa_is_alt_uom_finished_move() and m.lot_ids
        )
        for move in alt_finished:
            if not move._msa_lines_match_alt_uom_lots():
                move.production_id._msa_sync_finished_move_lots()

        packaging = self.filtered(
            lambda m: m not in alt_finished
            and m.product_id.tracking in ('serial', 'lot')
            and m._msa_uses_packaging_tracked_uom()
        )
        if packaging:
            self._msa_set_lot_ids_packaging(packaging)

        standard = self - alt_finished - packaging
        if standard:
            super(StockMove, standard)._set_lot_ids()

    def _msa_set_lot_ids_packaging(self, moves):
        """Assign lots on tracked moves that use a packaging/alternate UOM."""
        for move in moves:
            sml_uom_id, sml_qty = move._get_packaging_sml_uom_and_qty()
            commands = []
            free_lines = move.move_line_ids.filtered(lambda ml: not ml.lot_id)
            for lot in move.lot_ids:
                existing = move.move_line_ids.filtered(lambda ml: ml.lot_id == lot)
                if existing:
                    existing.write({'quantity': sml_qty, 'product_uom_id': sml_uom_id})
                elif free_lines[:1]:
                    line = free_lines[:1]
                    commands.append(Command.update(line.id, {
                        'lot_id': lot.id,
                        'product_uom_id': sml_uom_id,
                        'quantity': sml_qty,
                    }))
                    free_lines -= line
                else:
                    vals = move._prepare_move_line_vals(quantity=0)
                    vals.update({
                        'lot_id': lot.id,
                        'product_uom_id': sml_uom_id,
                        'quantity': sml_qty,
                    })
                    commands.append(Command.create(vals))
            if commands:
                move.write({'move_line_ids': commands})

    def _set_quantity_done_prepare_vals(self, qty):
        self.ensure_one()
        if not self._msa_uses_packaging_tracked_uom():
            return super()._set_quantity_done_prepare_vals(qty)
        sml_uom_id, sml_qty = self._get_packaging_sml_uom_and_qty()
        line_count = self._msa_alt_uom_line_count(qty)
        res = [Command.delete(ml.id) for ml in self.move_line_ids]
        for _i in range(line_count):
            vals = self._prepare_move_line_vals(quantity=0)
            vals['quantity'] = sml_qty
            vals['product_uom_id'] = sml_uom_id
            res.append(Command.create(vals))
        return res

    def _set_quantity(self):
        """Keep correct multi-lot lines when core writes MO qty in the wrong UOM."""
        preserve = self.filtered(lambda m: m._msa_lines_match_alt_uom_lots())
        process = self - preserve
        if process:
            super(StockMove, process)._set_quantity()
        if preserve:
            preserve._compute_quantity()
