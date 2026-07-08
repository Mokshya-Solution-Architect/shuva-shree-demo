from odoo import fields, models

class ShuvaReturnReason(models.Model):
    _name = 'shuva.return.reason'
    _description = 'Return Reason and Routing'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    return_type = fields.Selection([
        ('normal', 'Normal Resaleable Return'),
        ('expiry', 'Expiry'),
        ('breakage', 'Breakage / Damaged'),
        ('repack', 'Repack Required'),
    ], default='normal', required=True)
    location_dest_id = fields.Many2one('stock.location', string='Return Destination Location')
    create_credit_note = fields.Boolean(default=True)
    active = fields.Boolean(default=True)
