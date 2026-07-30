import logging

from odoo import api, models
from odoo.exceptions import UserError
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _msa_is_alt_uom_mo(self):
        self.ensure_one()
        return bool(
            self.product_uom_id
            and self.product_id.uom_id
            and self.product_uom_id != self.product_id.uom_id
        )

    def _msa_alt_uom_factor(self):
        self.ensure_one()
        return self.product_uom_id._compute_quantity(1.0, self.product_id.uom_id)

    def _msa_get_finished_move(self):
        self.ensure_one()
        return self.move_finished_ids.filtered(lambda m: m.product_id == self.product_id)

    def _msa_sync_finished_move_lots(self):
        """One move line per lot, each holding the base-UOM equivalent of 1 MO unit."""
        for production in self:
            if not (
                production._msa_is_alt_uom_mo()
                and production.product_tracking == 'lot'
                and production.lot_producing_ids
            ):
                continue
            finish_move = production._msa_get_finished_move()
            if not finish_move or finish_move._msa_lines_match_alt_uom_lots():
                continue

            factor = production._msa_alt_uom_factor()
            base_uom = production.product_id.uom_id
            finish_move.write({
                'move_line_ids': [Command.clear()] + [
                    Command.create({
                        'product_id': finish_move.product_id.id,
                        'product_uom_id': base_uom.id,
                        'quantity': factor,
                        'lot_id': lot.id,
                        'location_id': finish_move.location_id.id,
                        'location_dest_id': finish_move.location_dest_id.id,
                        'company_id': finish_move.company_id.id,
                    })
                    for lot in production.lot_producing_ids
                ],
            })
            finish_move._compute_quantity()
            _logger.debug(
                "[msa_mrp_serial_uom] synced %s lots × %s %s on %s",
                len(production.lot_producing_ids),
                factor,
                base_uom.name,
                production.name,
            )

    def _msa_serial_alt_uom_blocked(self):
        self.ensure_one()
        if self.product_tracking != 'serial' or not self._msa_is_alt_uom_mo():
            return False
        return self.product_id.uom_id.compare(self._msa_alt_uom_factor(), 1.0) > 0

    def _msa_raise_serial_alt_uom_error(self):
        self.ensure_one()
        factor = self._msa_alt_uom_factor()
        raise UserError(self.env._(
            "Cannot produce %(product)s in %(mo_uom)s with Serial Number tracking.\n\n"
            "1 %(mo_uom)s = %(factor)s %(base_uom)s, but Odoo serials may only hold "
            "1.0 %(base_uom)s in inventory.\n\n"
            "Fix: set the product tracking to \"By Lots\", then use Generate to create "
            "one unique lot per %(mo_uom)s (e.g. 50 %(mo_uom)s → 50 lots).",
            product=self.product_id.display_name,
            mo_uom=self.product_uom_id.display_name,
            factor=factor,
            base_uom=self.product_id.uom_id.display_name,
        ))

    def action_confirm(self):
        serial_alt_uom = {
            production.id: (production.product_qty, production.product_uom_id)
            for production in self
            if production.product_tracking == 'serial'
            and production.product_uom_id != production.product_id.uom_id
        }
        result = super().action_confirm()
        if not serial_alt_uom:
            return result

        for production in self.filtered(lambda p: p.id in serial_alt_uom):
            orig_qty, orig_uom = serial_alt_uom[production.id]
            production.write({
                'product_qty': orig_qty,
                'product_uom_id': orig_uom.id,
            })
            finished_moves = production.move_finished_ids.filtered(
                lambda m: m.product_id == production.product_id
            )
            if finished_moves:
                finished_moves.write({
                    'product_uom_qty': orig_qty,
                    'product_uom': orig_uom.id,
                })
        return result

    def action_generate_serial(self, workorder=False):
        self.ensure_one()
        if self._msa_serial_alt_uom_blocked():
            self._msa_raise_serial_alt_uom_error()

        if self.product_tracking == 'lot' and (
            self._msa_is_alt_uom_mo() or self.product_uom_id.compare(self.product_qty, 1.0) > 0
        ):
            action = self.env['ir.actions.actions']._for_xml_id('mrp.action_assign_serial_numbers')
            action['name'] = self.env._('Generate Lot Numbers')
            action['context'] = {
                'default_production_id': self.id,
                'msa_multi_lot_mode': True,
            }
            if workorder:
                action['context']['default_workorder_id'] = workorder.id
            return action

        return super().action_generate_serial(workorder=workorder)

    @api.constrains('lot_producing_ids')
    def _check_lot_producing_ids(self):
        for record in self:
            if record.product_tracking != 'lot':
                continue
            if len(record.lot_producing_ids) <= 1:
                continue
            if record._msa_is_alt_uom_mo() or self.env.context.get('msa_multi_lot_mode'):
                continue
            raise UserError(self.env._('You cannot set more than 1 lot'))

    def pre_button_mark_done(self):
        for production in self:
            if production._msa_serial_alt_uom_blocked():
                production._msa_raise_serial_alt_uom_error()
            if not (
                production.product_tracking == 'lot'
                and production._msa_is_alt_uom_mo()
                and production.lot_producing_ids
            ):
                continue
            expected = int(production.product_uom_id.round(
                production.product_qty, rounding_method='HALF-UP',
            ))
            if len(production.lot_producing_ids) != expected:
                raise UserError(self.env._(
                    "Expected %(expected)s unique lots (one per %(uom)s), but this MO has %(actual)s.\n\n"
                    "Click Clear, then Generate Lots → Generate → Apply to create %(expected)s lots.",
                    expected=expected,
                    uom=production.product_uom_id.display_name,
                    actual=len(production.lot_producing_ids),
                ))
        return super().pre_button_mark_done()

    def _post_inventory(self, cancel_backorder=False):
        self.filtered(
            lambda p: p.product_tracking == 'lot'
            and p._msa_is_alt_uom_mo()
            and p.lot_producing_ids
        )._msa_sync_finished_move_lots()
        return super()._post_inventory(cancel_backorder=cancel_backorder)

    def _set_qty_producing(self, pick_manual_consumption_moves=True):
        result = super()._set_qty_producing(
            pick_manual_consumption_moves=pick_manual_consumption_moves,
        )
        self.filtered(
            lambda p: p.product_tracking == 'lot'
            and p._msa_is_alt_uom_mo()
            and p.lot_producing_ids
        )._msa_sync_finished_move_lots()
        return result
