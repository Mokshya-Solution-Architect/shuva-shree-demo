from odoo import fields, models


class ShuvaPackType(models.Model):
    _name = 'shuva.pack.type'
    _description = 'Physical Pack / Alt Unit Type'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    notes = fields.Text()

    is_variable_qty = fields.Boolean(string="Variable Quantity Pack")
    average_qty_per_pack = fields.Float(string="Average Qty per Pack")
    fixed_qty_per_pack = fields.Float(string="Fixed Qty per Pack")
    uom_id = fields.Many2one('uom.uom', string="Stock UoM")

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Pack type code must be unique.'),
    ]