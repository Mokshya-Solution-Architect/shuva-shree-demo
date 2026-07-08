from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ShuvaPackLotWizard(models.TransientModel):
    _name = 'shuva.pack.lot.wizard'
    _description = 'Generate Pack Lots / Barcodes for Receipt'

    move_id = fields.Many2one('stock.move', required=True)
    product_id = fields.Many2one(related='move_id.product_id', readonly=True)
    picking_id = fields.Many2one(related='move_id.picking_id', readonly=True)

    pack_type_id = fields.Many2one('shuva.pack.type', string='Pack Type')
    pack_count = fields.Integer(string='Number of Packs', default=1, required=True)
    total_qty = fields.Float(string='Total Quantity', digits='Product Unit of Measure')
    distribute_equally = fields.Boolean(default=True)

    line_ids = fields.One2many(
        'shuva.pack.lot.wizard.line',
        'wizard_id',
        string='Pack Lines',
    )

    @api.onchange('move_id')
    def _onchange_move_id(self):
        for wizard in self:
            if wizard.move_id:
                wizard.total_qty = wizard.move_id.quantity or wizard.move_id.product_uom_qty
                wizard.pack_count = int(wizard.move_id.shuva_alt_qty or 1)
                wizard.pack_type_id = (
                    wizard.move_id.shuva_pack_type_id
                    or wizard.move_id.product_id.product_tmpl_id.shuva_default_pack_type_id
                )

    def action_prepare_lines(self):
        self.ensure_one()

        if self.pack_count <= 0:
            raise UserError(_('Pack count must be greater than zero.'))

        qty_each = self.total_qty / self.pack_count if self.distribute_equally else 0.0

        self.line_ids = [(5, 0, 0)]

        lines = []
        for i in range(self.pack_count):
            lines.append((0, 0, {
                'sequence': i + 1,
                'name': _('Pack %s') % (i + 1),
                'qty': qty_each,
            }))

        self.line_ids = lines

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_generate(self):
        self.ensure_one()

        if not self.line_ids:
            self.action_prepare_lines()

        if not self.line_ids:
            raise UserError(_('Please prepare pack lines first.'))

        actual_total_qty = sum(self.line_ids.mapped('qty'))

        if actual_total_qty <= 0:
            raise UserError(_('Actual total quantity must be greater than zero.'))

        StockLot = self.env['stock.lot']
        MoveLine = self.env['stock.move.line']

        self.move_id.move_line_ids.unlink()

        supplier = False
        purchase = False

        if self.move_id.purchase_line_id:
            purchase = self.move_id.purchase_line_id.order_id
            supplier = purchase.partner_id

        for line in self.line_ids:
            if line.qty <= 0:
                raise UserError(_('Every pack line must have a positive quantity.'))

            barcode = line.vendor_barcode or StockLot.shuva_next_pack_barcode(
                self.product_id,
                self.pack_type_id
            )

            lot = StockLot.create({
                'name': barcode,
                'product_id': self.product_id.id,
                'company_id': self.picking_id.company_id.id,
                'shuva_pack_barcode': barcode,
                'shuva_is_generated_pack': not bool(line.vendor_barcode),
                'shuva_pack_type_id': self.pack_type_id.id,
                'shuva_pack_qty': line.qty,
                'shuva_alt_qty': 1,
                'shuva_supplier_id': supplier.id if supplier else False,
                'shuva_purchase_id': purchase.id if purchase else False,
                'shuva_received_date': fields.Datetime.now(),
            })

            MoveLine.create({
                'move_id': self.move_id.id,
                'picking_id': self.picking_id.id,
                'product_id': self.product_id.id,
                'product_uom_id': self.move_id.product_uom.id,
                'quantity': line.qty,
                'lot_id': lot.id,
                'location_id': self.move_id.location_id.id,
                'location_dest_id': self.move_id.location_dest_id.id,
            })

        self.move_id.product_uom_qty = actual_total_qty
        self.move_id.quantity = actual_total_qty
        self.move_id.shuva_actual_received_qty = actual_total_qty

        if self.move_id.purchase_line_id:
            self.move_id.purchase_line_id.product_qty = actual_total_qty
            self.move_id.purchase_line_id.shuva_actual_received_qty = actual_total_qty

        return {'type': 'ir.actions.act_window_close'}


class ShuvaPackLotWizardLine(models.TransientModel):
    _name = 'shuva.pack.lot.wizard.line'
    _description = 'Pack Lot Wizard Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'shuva.pack.lot.wizard',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Sequence')
    name = fields.Char()
    qty = fields.Float(required=True, digits='Product Unit of Measure')
    vendor_barcode = fields.Char(string='Existing Vendor Barcode')