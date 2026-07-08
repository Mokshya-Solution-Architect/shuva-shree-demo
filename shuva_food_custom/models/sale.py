from odoo import models

class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'shuva.alt.unit.mixin']

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            for picking in order.picking_ids:
                for move in picking.move_ids_without_package:
                    sol = move.sale_line_id
                    if sol:
                        move.shuva_alt_qty = sol.shuva_alt_qty
                        move.shuva_pack_type_id = sol.shuva_pack_type_id.id
                        move.shuva_pack_note = sol.shuva_pack_note
        return res
