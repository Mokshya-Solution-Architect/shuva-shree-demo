# -*- coding: utf-8 -*-
from odoo import models
 
 
class StockRule(models.Model):
    _inherit = 'stock.rule'
 
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values):
        move_vals = super()._get_stock_move_values(
            product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values
        )
        sol_ref = values.get('sale_line_id')
        if not sol_ref:
            return move_vals
        sol = self.env['sale.order.line'].browse(sol_ref) if isinstance(sol_ref, int) else sol_ref
        if not sol or not sol.product_uom_id:
            return move_vals
 
        line_uom = sol.product_uom_id
        move_uom = self.env['uom.uom'].browse(move_vals['product_uom'])
        if move_uom == line_uom:
            return move_vals
        if not move_uom._has_common_reference(line_uom):
            return move_vals
 
        qty = move_vals.get('product_uom_qty') or 0.0
        qty_line = move_uom._compute_quantity(
            qty, line_uom, round=True, rounding_method='HALF-UP', raise_if_failure=False
        )
        move_vals['product_uom'] = line_uom.id
        move_vals['product_uom_qty'] = line_uom.round(qty_line)
        return move_vals