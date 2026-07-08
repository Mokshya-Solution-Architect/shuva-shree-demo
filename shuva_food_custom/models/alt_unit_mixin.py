from odoo import fields, models


class ShuvaAltUnitMixin(models.AbstractModel):
    _name = 'shuva.alt.unit.mixin'
    _description = 'Alt Unit Fields Mixin'

    shuva_alt_qty = fields.Float(string='Alt Qty / Pack Count', digits='Product Unit of Measure')
    shuva_pack_type_id = fields.Many2one('shuva.pack.type', string='Alt Unit / Pack Type')
    shuva_pack_note = fields.Char(string='Alt Unit Note')

    shuva_avg_qty_per_pack = fields.Float(string="Average Qty per Pack")
    shuva_estimated_qty = fields.Float(string="Estimated Qty")
    shuva_actual_received_qty = fields.Float(string="Actual Received Qty")