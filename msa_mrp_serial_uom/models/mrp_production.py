import logging

from odoo import api, models
from odoo.exceptions import UserError

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

        for production in self:
            _logger.warning(
                "[msa_mrp_serial_uom] action_confirm BEFORE | MO=%s tracking=%s "
                "qty=%s uom=%s will_restore=%s serial_blocked=%s",
                production.name,
                production.product_tracking,
                production.product_qty,
                production.product_uom_id.display_name,
                production.id in serial_alt_uom,
                production._msa_serial_alt_uom_blocked(),
            )

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
            _logger.warning(
                "[msa_mrp_serial_uom] action_confirm RESTORED | MO=%s qty=%s uom=%s",
                production.name,
                production.product_qty,
                production.product_uom_id.display_name,
            )

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
            _logger.warning(
                "[msa_mrp_serial_uom] action_generate_serial → multi-lot wizard | MO=%s "
                "qty=%s uom=%s",
                self.name,
                self.product_qty,
                self.product_uom_id.display_name,
            )
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
                _logger.warning(
                    "[msa_mrp_serial_uom] allowing %s lots on MO %s (alt_uom=%s)",
                    len(record.lot_producing_ids),
                    record.name,
                    record.product_uom_id.display_name,
                )
                continue
            raise UserError(self.env._('You cannot set more than 1 lot'))

    def pre_button_mark_done(self):
        for production in self:
            if production._msa_serial_alt_uom_blocked():
                production._msa_raise_serial_alt_uom_error()
            if (
                production.product_tracking == 'lot'
                and production._msa_is_alt_uom_mo()
                and production.lot_producing_ids
            ):
                expected = int(production.product_uom_id.round(
                    production.product_qty, rounding_method='HALF-UP',
                ))
                actual = len(production.lot_producing_ids)
                if actual != expected:
                    raise UserError(self.env._(
                        "Expected %(expected)s unique lots (one per %(uom)s), but this MO has %(actual)s.\n\n"
                        "Click Clear, then Generate Lots → Generate → Apply to create %(expected)s lots.",
                        expected=expected,
                        uom=production.product_uom_id.display_name,
                        actual=actual,
                    ))
        return super().pre_button_mark_done()

    def _post_inventory(self, cancel_backorder=False):
        for order in self:
            finish_moves = order.move_finished_ids.filtered(
                lambda m: m.product_id == order.product_id and m.state not in ('done', 'cancel')
            )
            _logger.warning(
                "[msa_mrp_serial_uom] _post_inventory ENTER | MO=%s tracking=%s "
                "qty_producing=%s product_qty=%s uom=%s lot_count=%s "
                "finish_sml_with_lot=%s finish_sml_without_lot=%s",
                order.name,
                order.product_tracking,
                order.qty_producing,
                order.product_qty,
                order.product_uom_id.display_name,
                len(order.lot_producing_ids),
                sum(len(m.move_line_ids.filtered('lot_id')) for m in finish_moves),
                sum(len(m.move_line_ids.filtered(lambda l: not l.lot_id)) for m in finish_moves),
            )
        return super()._post_inventory(cancel_backorder=cancel_backorder)

    def _set_qty_producing(self, pick_manual_consumption_moves=True):
        for production in self:
            _logger.warning(
                "[msa_mrp_serial_uom] _set_qty_producing ENTER | MO=%s tracking=%s "
                "qty_producing=%s product_qty=%s uom=%s lot_count=%s",
                production.name,
                production.product_tracking,
                production.qty_producing,
                production.product_qty,
                production.product_uom_id.display_name,
                len(production.lot_producing_ids),
            )
        result = super()._set_qty_producing(pick_manual_consumption_moves=pick_manual_consumption_moves)
        for production in self:
            finished = production.move_finished_ids.filtered(
                lambda m: m.product_id == production.product_id
            )
            _logger.warning(
                "[msa_mrp_serial_uom] _set_qty_producing EXIT | MO=%s sml_total=%s "
                "with_lot=%s without_lot=%s",
                production.name,
                sum(len(m.move_line_ids) for m in finished),
                sum(len(m.move_line_ids.filtered('lot_id')) for m in finished),
                sum(len(m.move_line_ids.filtered(lambda l: not l.lot_id)) for m in finished),
            )
        return result
