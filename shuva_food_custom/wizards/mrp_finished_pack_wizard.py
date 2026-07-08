from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ShuvaMrpFinishedPackWizard(models.TransientModel):
    _name = 'shuva.mrp.finished.pack.wizard'
    _description = 'Generate Finished Good Pack Barcodes'

    production_id = fields.Many2one('mrp.production', required=True)
    product_id = fields.Many2one(related='production_id.product_id', readonly=True)
    pack_type_id = fields.Many2one('shuva.pack.type', string='Pack Type')
    qty_per_pack = fields.Float(string='Qty per Pack', required=True, digits='Product Unit of Measure')
    pack_count = fields.Integer(string='Pack Count', compute='_compute_pack_count', store=False)
    total_qty = fields.Float(string='Finished Quantity', digits='Product Unit of Measure')

    @api.onchange('production_id')
    def _onchange_production_id(self):
        if self.production_id:
            tmpl = self.production_id.product_id.product_tmpl_id
            self.total_qty = self.production_id.qty_producing or self.production_id.product_qty
            self.qty_per_pack = self.production_id.shuva_finished_pack_qty or tmpl.shuva_default_pack_qty or tmpl.shuva_pos_pack_scan_qty or 1.0
            self.pack_type_id = self.production_id.shuva_pack_type_id or tmpl.shuva_default_pack_type_id

    @api.depends('total_qty', 'qty_per_pack')
    def _compute_pack_count(self):
        for wiz in self:
            wiz.pack_count = int((wiz.total_qty + wiz.qty_per_pack - 0.000001) // wiz.qty_per_pack) if wiz.qty_per_pack else 0

    def action_generate(self):
        self.ensure_one()
        if self.qty_per_pack <= 0:
            raise UserError(_('Qty per pack must be greater than zero.'))
        finished_move = self.production_id.move_finished_ids.filtered(lambda m: m.product_id == self.product_id)[:1]
        if not finished_move:
            raise UserError(_('No finished stock move found for this production.'))
        finished_move.move_line_ids.unlink()
        remaining = self.total_qty
        StockLot = self.env['stock.lot']
        MoveLine = self.env['stock.move.line']
        while remaining > 0:
            qty = min(self.qty_per_pack, remaining)
            lot = StockLot.create({
                'product_id': self.product_id.id,
                'company_id': self.production_id.company_id.id,
                'shuva_is_generated_pack': True,
                'shuva_pack_type_id': self.pack_type_id.id,
                'shuva_pack_qty': qty,
                'shuva_alt_qty': 1,
                'shuva_mrp_production_id': self.production_id.id,
                'shuva_received_date': fields.Datetime.now(),
            })
            MoveLine.create({
                'move_id': finished_move.id,
                'product_id': self.product_id.id,
                'product_uom_id': finished_move.product_uom.id,
                'quantity': qty,
                'lot_id': lot.id,
                'location_id': finished_move.location_id.id,
                'location_dest_id': finished_move.location_dest_id.id,
            })
            remaining -= qty
        return {'type': 'ir.actions.act_window_close'}
