from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shuva_requires_pack_lot = fields.Boolean(string='Require Unique Pack Barcode')
    shuva_default_pack_type_id = fields.Many2one('shuva.pack.type', string='Default Pack Type')
    shuva_default_pack_qty = fields.Float(string='Default Qty per Pack')
    shuva_pos_pack_scan_qty = fields.Float(string='POS Qty When Pack Barcode Scanned')

    shuva_average_qty_per_pack = fields.Float(
        string="Average Qty per Pack",
        help="Used to estimate PO quantity from Alt Qty."
    )