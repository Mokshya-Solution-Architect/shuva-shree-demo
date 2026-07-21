import logging

from odoo import models
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _msa_uses_packaging_tracked_uom(self):
        self.ensure_one()
        return (
            self.product_id.tracking in ('serial', 'lot')
            and self.product_uom
            and self.product_uom != self.product_id.uom_id
        )

    def _get_packaging_sml_uom_and_qty(self):
        self.ensure_one()
        if self._msa_uses_packaging_tracked_uom():
            return self.product_uom.id, 1.0
        if self.product_id.tracking == 'serial':
            return self.product_id.uom_id.id, 1.0
        return self.product_uom.id, self.quantity

    def _set_lot_ids(self):
        for move in self:
            if move.state == 'assigned' and all(ml.lot_id in move.lot_ids for ml in move.move_line_ids):
                _logger.warning(
                    "[msa_mrp_serial_uom] _set_lot_ids SKIP | move=%s sml=%s",
                    move.id,
                    len(move.move_line_ids),
                )
                continue

            if move.product_id.tracking in ('serial', 'lot') and move._msa_uses_packaging_tracked_uom():
                sml_uom_id, sml_qty = move._get_packaging_sml_uom_and_qty()
            elif move.product_id.tracking == 'serial':
                sml_uom_id, sml_qty = move.product_id.uom_id.id, 1.0
            else:
                sml_uom_id = move.product_uom.id
                sml_qty = move.quantity

            _logger.warning(
                "[msa_mrp_serial_uom] _set_lot_ids ENTER | move=%s product=%s tracking=%s "
                "move.uom=%s sml_uom_id=%s sml_qty=%s lot_count=%s existing_sml=%s",
                move.id,
                move.product_id.display_name,
                move.product_id.tracking,
                move.product_uom.display_name,
                sml_uom_id,
                sml_qty,
                len(move.lot_ids),
                len(move.move_line_ids),
            )

            move_lines_commands = []
            mls = move.move_line_ids
            mls_with_lots = mls.filtered(lambda ml: ml.lot_id)
            mls_without_lots = mls - mls_with_lots
            for ml in mls_with_lots:
                if ml.quantity and ml.lot_id not in move.lot_ids:
                    move_lines_commands.append(Command.delete(ml.id))
            ls = move.move_line_ids.lot_id
            for lot in move.lot_ids:
                if lot not in ls:
                    if mls_without_lots[:1]:
                        move_line = mls_without_lots[:1]
                        move_lines_commands.append(Command.update(move_line.id, {
                            'lot_id': lot.id,
                            'product_uom_id': sml_uom_id,
                            'quantity': sml_qty,
                        }))
                        mls_without_lots -= move_line
                    else:
                        reserved_quants = self.env['stock.quant'].with_context(
                            packaging_uom_id=move.packaging_uom_id,
                        )._get_reserve_quantity(move.product_id, move.location_id, 1.0, lot_id=lot)
                        if reserved_quants and reserved_quants[0][0].lot_id:
                            move_line_vals = self._prepare_move_line_vals(
                                quantity=0, reserved_quant=reserved_quants[0][0],
                            )
                        else:
                            move_line_vals = self._prepare_move_line_vals(quantity=0)
                            move_line_vals['lot_id'] = lot.id
                        move_line_vals['product_uom_id'] = sml_uom_id
                        move_line_vals['quantity'] = sml_qty
                        move_lines_commands.append(Command.create(move_line_vals))
                else:
                    move_line = move.move_line_ids.filtered(lambda line: line.lot_id.id == lot.id)
                    if move._msa_uses_packaging_tracked_uom():
                        move_line.quantity = sml_qty
                    elif move.product_id.tracking == 'serial':
                        move_line.quantity = 1
            move.write({'move_line_ids': move_lines_commands})

            _logger.warning(
                "[msa_mrp_serial_uom] _set_lot_ids EXIT | move=%s sml=%s with_lot=%s without_lot=%s",
                move.id,
                len(move.move_line_ids),
                len(move.move_line_ids.filtered('lot_id')),
                len(move.move_line_ids.filtered(lambda l: not l.lot_id)),
            )

    def _set_quantity_done_prepare_vals(self, qty):
        self.ensure_one()
        if self._msa_uses_packaging_tracked_uom():
            sml_uom_id, sml_qty = self._get_packaging_sml_uom_and_qty()
            serial_count = int(self.product_uom.round(qty, rounding_method='HALF-UP'))
            res = [Command.delete(ml.id) for ml in self.move_line_ids]
            for _i in range(serial_count):
                vals = self._prepare_move_line_vals(quantity=0)
                vals['quantity'] = sml_qty
                vals['product_uom_id'] = sml_uom_id
                res.append(Command.create(vals))
            _logger.warning(
                "[msa_mrp_serial_uom] _set_quantity_done_prepare_vals PACKAGING | move=%s "
                "tracking=%s qty=%s uom=%s count=%s",
                self.id,
                self.product_id.tracking,
                qty,
                self.product_uom.display_name,
                serial_count,
            )
            return res
        return super()._set_quantity_done_prepare_vals(qty)

    def _set_quantity_done(self, qty):
        for move in self:
            if move._msa_uses_packaging_tracked_uom() or move.product_id.tracking == 'serial':
                _logger.warning(
                    "[msa_mrp_serial_uom] _set_quantity_done ENTER | move=%s tracking=%s "
                    "qty=%s uom=%s packaging=%s",
                    move.id,
                    move.product_id.tracking,
                    qty,
                    move.product_uom.display_name,
                    move._msa_uses_packaging_tracked_uom(),
                )
        result = super()._set_quantity_done(qty)
        for move in self:
            if move._msa_uses_packaging_tracked_uom() or move.product_id.tracking == 'serial':
                _logger.warning(
                    "[msa_mrp_serial_uom] _set_quantity_done EXIT | move=%s sml=%s "
                    "with_lot=%s without_lot=%s",
                    move.id,
                    len(move.move_line_ids),
                    len(move.move_line_ids.filtered('lot_id')),
                    len(move.move_line_ids.filtered(lambda l: not l.lot_id)),
                )
        return result
