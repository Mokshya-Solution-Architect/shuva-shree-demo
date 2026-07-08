from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockLot(models.Model):
    _inherit = 'stock.lot'

    shuva_pack_barcode = fields.Char(string='Pack Barcode', copy=False, index=True)
    shuva_pack_type_id = fields.Many2one('shuva.pack.type', string='Pack Type')
    shuva_pack_qty = fields.Float(string='Pack Quantity', digits='Product Unit of Measure')
    shuva_alt_qty = fields.Float(string='Alt Qty / Pack Count', digits='Product Unit of Measure')
    shuva_supplier_id = fields.Many2one('res.partner', string='Supplier')
    shuva_purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    shuva_mrp_production_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    shuva_received_date = fields.Datetime(string='Received/Produced Date')
    shuva_is_generated_pack = fields.Boolean(string='Generated Pack Barcode', default=False)

    _sql_constraints = [
        ('shuva_pack_barcode_unique', 'unique(shuva_pack_barcode)', 'Pack barcode must be unique.'),
    ]

    @api.model
    def shuva_next_pack_barcode(self, product=False, pack_type=False):
        code = self.env['ir.sequence'].next_by_code('shuva.pack.barcode') or '/'
        prefix = ''
        if pack_type and pack_type.code:
            prefix = pack_type.code.upper()
        elif product and product.default_code:
            prefix = product.default_code[:4].upper()
        return f'{prefix}{code}' if prefix else code

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('shuva_pack_barcode') and vals.get('shuva_is_generated_pack'):
                product = self.env['product.product'].browse(vals.get('product_id')) if vals.get('product_id') else False
                pack_type = self.env['shuva.pack.type'].browse(vals.get('shuva_pack_type_id')) if vals.get('shuva_pack_type_id') else False
                vals['shuva_pack_barcode'] = self.shuva_next_pack_barcode(product, pack_type)
                vals.setdefault('name', vals['shuva_pack_barcode'])
        return super().create(vals_list)

    def name_get(self):
        result = []
        for lot in self:
            name = lot.name
            if lot.shuva_pack_barcode and lot.shuva_pack_barcode != lot.name:
                name = f'{lot.name} [{lot.shuva_pack_barcode}]'
            result.append((lot.id, name))
        return result

    @api.constrains('shuva_pack_qty')
    def _check_pack_qty(self):
        for lot in self:
            if lot.shuva_pack_qty < 0:
                raise ValidationError(_('Pack quantity cannot be negative.'))

    @api.model
    def shuva_pos_lookup_pack_barcode(self, barcode):
        lot = self.search(['|', ('shuva_pack_barcode', '=', barcode), ('name', '=', barcode)], limit=1)
        if not lot:
            return False
        product = lot.product_id
        qty = product.shuva_pos_pack_scan_qty or lot.shuva_pack_qty or 1.0
        return {
            'lot_id': lot.id,
            'lot_name': lot.name,
            'pack_barcode': lot.shuva_pack_barcode or lot.name,
            'product_id': product.id,
            'product_barcode': product.barcode,
            'qty': qty,
            'uom_name': product.uom_id.name,
        }
