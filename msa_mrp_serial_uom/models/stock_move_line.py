from odoo import models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _onchange_quantity(self):
        if (self.product_id.tracking == 'serial'
                and self.product_uom_id
                and self.product_uom_id != self.product_id.uom_id
                and self.product_id.uom_id.is_zero(self.quantity - 1.0)):
            return {}
        return super()._onchange_quantity()
