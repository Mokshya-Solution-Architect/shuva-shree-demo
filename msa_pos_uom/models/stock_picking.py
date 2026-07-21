# -*- coding: utf-8 -*-

from itertools import groupby

from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        """Override to use the line's selected UoM and convert qty to that UoM."""
        vals = super()._prepare_stock_move_vals(first_line, order_lines)
        line_uom = first_line.product_uom_id or first_line.product_id.uom_id
        base_uom = first_line.product_id.uom_id
        vals['product_uom'] = line_uom.id
        if line_uom != base_uom:
            # qty from super() is sum of line.qty (in base UoM when UoM = base,
            # or in line UoM when packaging). Convert to move UoM.
            raw_qty = abs(sum(order_lines.mapped('qty')))
            # line.qty is in line_uom; stock move also in line_uom — keep as is.
            vals['product_uom_qty'] = raw_qty
        return vals

    def _create_move_from_pos_order_lines(self, lines):
        """Override to group lines by (product, attributes, UoM) so different-UoM lines
        each get their own stock move with the correct unit."""
        self.ensure_one()

        def get_grouping_key(line):
            uom_id = (line.product_uom_id or line.product_id.uom_id).id
            return (line.product_id.id, tuple(sorted(line.attribute_value_ids.ids)), uom_id)

        lines_by_product_attrs_uom = groupby(
            sorted(lines, key=get_grouping_key),
            key=get_grouping_key,
        )
        move_vals = []
        for _key, olines in lines_by_product_attrs_uom:
            order_lines = self.env['pos.order.line'].concat(*olines)
            move_vals.append(self._prepare_stock_move_vals(order_lines[0], order_lines))

        moves = self.env['stock.move'].create(move_vals)
        confirmed_moves = moves._action_confirm()
        confirmed_moves._add_mls_related_to_order(lines, are_qties_done=True)
        confirmed_moves.picked = True
        self._link_owner_on_return_picking(lines)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _msa_pos_line_base_qty(self, line):
        """Return the qty to use for stock move line creation.

        `_prepare_move_line_vals` expects a quantity in the product's base UoM.
        POS order lines now store qty in the selected line UoM (e.g. Jhola),
        so we must convert before passing to the stock layer.
        Serial tracking always uses 1 regardless of UoM.
        """
        if line.product_id.tracking == 'serial':
            return 1
        line_uom = line.product_uom_id or line.product_id.uom_id
        base_uom = line.product_id.uom_id
        if line_uom and line_uom != base_uom:
            return line_uom._compute_quantity(abs(line.qty), base_uom)
        return abs(line.qty)

    def _add_mls_related_to_order(self, related_order_lines, are_qties_done=True):
        """Override to handle packaging UoM: convert line qty to base UoM before
        passing to _prepare_move_line_vals (which always expects base-UoM qty)."""
        lines_data = self._prepare_lines_data_dict(related_order_lines)
        moves_to_assign = self.filtered(
            lambda m: m.product_id.id not in lines_data
            or m.product_id.tracking == 'none'
            or (not m.picking_type_id.use_existing_lots and not m.picking_type_id.use_create_lots)
        )

        uoms_with_issues = set()
        for move in moves_to_assign.filtered(lambda m: m.product_uom_qty and m.product_uom != m.product_id.uom_id):
            converted_qty = move.product_uom._compute_quantity(
                move.product_uom_qty, move.product_id.uom_id, rounding_method='HALF-UP'
            )
            if not converted_qty:
                uoms_with_issues.add((move.product_uom.name, move.product_id.uom_id.name))

        if uoms_with_issues:
            error_message_lines = [_(
                "Conversion Error: The following unit of measure conversions result in a zero quantity due to rounding:"
            )]
            for uom_from, uom_to in uoms_with_issues:
                error_message_lines.append(_(
                    ' - From "%(uom_from)s" to "%(uom_to)s"', uom_from=uom_from, uom_to=uom_to
                ))
            error_message_lines.append(_(
                "\nThis issue occurs because the quantity becomes zero after rounding during the conversion. "
                "To fix this, adjust the conversion factors or rounding method to ensure that even the smallest "
                "quantity in the original unit does not round down to zero in the target unit."
            ))
            raise UserError('\n'.join(error_message_lines))

        for move in moves_to_assign:
            move.quantity = move.product_uom_qty
        moves_remaining = self - moves_to_assign
        existing_lots = moves_remaining._create_production_lots_for_pos_order(related_order_lines)
        move_lines_to_create = []
        if are_qties_done:
            for move in moves_remaining:
                move.move_line_ids.unlink()
                for line in lines_data[move.product_id.id]['order_lines']:
                    for lot in line.pack_lot_ids.filtered(lambda l: l.lot_name):
                        # KEY FIX: convert from line UoM to base UoM before passing
                        # to _prepare_move_line_vals (which expects base-UoM qty).
                        qty = self._msa_pos_line_base_qty(line)
                        if existing_lots:
                            existing_lot = existing_lots.filtered_domain([
                                ('product_id', '=', line.product_id.id),
                                ('name', '=', lot.lot_name),
                            ])
                            quants = self.env['stock.quant']
                            if existing_lot:
                                quants = self.env['stock.quant'].search(
                                    [('lot_id', '=', existing_lot.id), ('quantity', '>', '0.0'),
                                     ('location_id', 'child_of', move.location_id.id)],
                                    order='id desc',
                                )
                            qty_left_to_assign = qty
                            for quant in quants:
                                if qty_left_to_assign <= 0:
                                    break
                                qty_chg = min(qty_left_to_assign, quant.quantity)
                                ml_vals = dict(move._prepare_move_line_vals(qty_chg))
                                qty_left_to_assign -= qty_chg
                                ml_vals['quant_id'] = quant.id
                                move_lines_to_create.append(ml_vals)
                            if qty_left_to_assign > 0:
                                ml_vals = dict(move._prepare_move_line_vals(qty_left_to_assign))
                                ml_vals.update({'lot_name': existing_lot.name, 'lot_id': existing_lot.id})
                                move_lines_to_create.append(ml_vals)
                        else:
                            ml_vals = dict(move._prepare_move_line_vals(qty))
                            ml_vals['lot_name'] = lot.lot_name
                            move_lines_to_create.append(ml_vals)
            self.env['stock.move.line'].create(move_lines_to_create)
        else:
            for move in moves_remaining:
                for line in lines_data[move.product_id.id]['order_lines']:
                    for lot in line.pack_lot_ids.filtered(lambda l: l.lot_name):
                        qty = self._msa_pos_line_base_qty(line)
                        if existing_lots:
                            existing_lot = existing_lots.filtered_domain([
                                ('product_id', '=', line.product_id.id),
                                ('name', '=', lot.lot_name),
                            ])
                            if existing_lot:
                                move._update_reserved_quantity(qty, move.location_id, lot_id=existing_lot)
                                continue
