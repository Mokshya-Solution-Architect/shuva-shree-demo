# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _ss_lot_move_lines(self):
        """Lots may be on move lines without picking_id (e.g. VRW receipts)."""
        self.ensure_one()
        return self.env['stock.move.line'].search([
            ('lot_id', '!=', False),
            '|',
            ('picking_id', '=', self.id),
            ('move_id.picking_id', '=', self.id),
        ])

    def action_print_lot_sn_labels(self):
        """Open lot/SN barcode label wizard for this transfer's move lines."""
        self.ensure_one()
        lines = self._ss_lot_move_lines()
        if not lines:
            raise UserError(_('No lot/serial numbers on this transfer to print.'))
        view = self.env.ref('stock.lot_label_layout_form_picking')
        return {
            'name': _('Lot/SN Labels'),
            'type': 'ir.actions.act_window',
            'res_model': 'lot.label.layout',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': {
                'default_move_line_ids': lines.ids,
            },
        }
