# -*- coding: utf-8 -*-
from odoo import models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _get_available_quantity(self, product_id, location_id, lot_id=None,
                                package_id=None, owner_id=None,
                                strict=False, allow_negative=False):
        """Floor available quantity to whole packaging multiples when the
        reservation engine is operating with a coarser packaging UoM
        (e.g. CASE-of-EA on a SO/PO-driven move).

        Triggered only when ``packaging_uom_id`` is present in context, which
        ``stock.move._update_reserved_quantity_vals`` sets to the move's
        packaging UoM (in turn driven by the SO/PO line UoM). Other callers
        (free_qty widgets, forecasts, accounting, etc.) don't set this key,
        so they are unaffected.
        """
        qty = super()._get_available_quantity(
            product_id, location_id,
            lot_id=lot_id, package_id=package_id, owner_id=owner_id,
            strict=strict, allow_negative=allow_negative,
        )
        if strict:
            return qty
        packaging_uom = self.env.context.get('packaging_uom_id')
        base_uom = product_id.uom_id
        if (
            not packaging_uom
            or not base_uom
            or packaging_uom == base_uom
            or not packaging_uom._has_common_reference(base_uom)
        ):
            return qty
        if base_uom.compare(qty, 0) <= 0:
            return qty
        return packaging_uom._check_qty(qty, base_uom, 'DOWN')