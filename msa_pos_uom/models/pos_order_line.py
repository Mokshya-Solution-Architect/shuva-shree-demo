# -*- coding: utf-8 -*-

from itertools import groupby

from odoo import api, fields, models
from odoo.orm.commands import Command


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    # Convert from related (always base UoM) to a stored, writable field.
    # This lets cashiers sell in packaging UoMs without touching base qty/price logic.
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Product Unit of Measure',
        ondelete='restrict',
        store=True,
        related=False,
        readonly=False,
        compute=False,
        compute_sudo=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('product_uom_id') and vals.get('product_id'):
                product = self.env['product.product'].browse(vals['product_id'])
                vals['product_uom_id'] = product.uom_id.id
        return super().create(vals_list)

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        if 'product_uom_id' not in fields:
            fields.append('product_uom_id')
        return fields

    def _launch_stock_rule_from_pos_order_lines(self):
        """Override to use line.product_uom_id for procurement instead of hardcoded base UoM."""
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.product_id.type != 'consu':
                continue

            reference_ids = line.order_id.stock_reference_ids
            if not reference_ids:
                reference_ids = self.env['stock.reference'].create(line._prepare_reference_vals())
                line.order_id.stock_reference_ids = [Command.set(reference_ids.ids)]

            values = line._prepare_procurement_values()
            product_qty = line.qty
            # Use the selected line UoM (packaging) rather than hardcoded base UoM.
            procurement_uom = line.product_uom_id or line.product_id.uom_id
            procurements.append(self.env['stock.rule'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_id.property_stock_customer,
                line.name, line.order_id.name, line.order_id.company_id, values))

        if procurements:
            self.env['stock.rule'].run(procurements)

        # Trigger scheduler for pickings (unchanged from core).
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids
            if pickings_to_confirm:
                tracked_lines = order.lines.filtered(lambda l: l.product_id.tracking != 'none')
                lines_by_tracked_product = groupby(
                    sorted(tracked_lines, key=lambda l: l.product_id.id),
                    key=lambda l: l.product_id.id,
                )
                pickings_to_confirm.action_confirm()
                for product_id, lines in lines_by_tracked_product:
                    lines = self.env['pos.order.line'].concat(*lines)
                    moves = pickings_to_confirm.move_ids.filtered(
                        lambda m: m.product_id.id == product_id
                    )
                    moves.move_line_ids.unlink()
                    moves._add_mls_related_to_order(lines, are_qties_done=False)
                    moves._recompute_state()
        return True
