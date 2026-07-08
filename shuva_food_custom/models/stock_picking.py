from odoo import fields, models


class StockMove(models.Model):
    _inherit = ['stock.move', 'shuva.alt.unit.mixin']

    def action_open_shuva_pack_lot_wizard(self):
        self.ensure_one()

        lines = []
        alt_qty = int(self.shuva_alt_qty or 0)
        avg_qty = self.shuva_avg_qty_per_pack or self.shuva_pack_type_id.average_qty_per_pack or 0.0

        for i in range(alt_qty):
            lines.append((0, 0, {
                'sequence': i + 1,
                'qty': avg_qty,
            }))

        return {
            'name': 'Enter Actual Pack Quantities',
            'type': 'ir.actions.act_window',
            'res_model': 'shuva.pack.lot.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
                'default_line_ids': lines,
            },
        }


class StockMoveLine(models.Model):
    _inherit = ['stock.move.line', 'shuva.alt.unit.mixin']

    shuva_pack_barcode = fields.Char(
        related='lot_id.shuva_pack_barcode',
        string='Pack Barcode',
        store=True,
        readonly=True,
    )
    shuva_pack_qty = fields.Float(
        related='lot_id.shuva_pack_qty',
        string='Pack Qty',
        store=True,
        readonly=True,
    )


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shuva_return_reason_id = fields.Many2one('shuva.return.reason', string='Return Reason')

    def action_generate_pack_lots(self):
        self.ensure_one()
        move = self.move_ids.filtered(
            lambda m: m.product_id.tracking == 'lot' and m.shuva_alt_qty
        )[:1]
        return move.action_open_shuva_pack_lot_wizard() if move else False