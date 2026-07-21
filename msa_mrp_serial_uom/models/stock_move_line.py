import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _onchange_quantity(self):
        if (self.product_id.tracking == 'serial'
                and self.product_uom_id
                and self.product_uom_id != self.product_id.uom_id
                and self.product_id.uom_id.is_zero(self.quantity - 1.0)):
            return {}
        return super()._onchange_quantity()

    def _action_done(self):
        tracked = self.filtered(lambda ml: ml.product_id.tracking != 'none' and ml.quantity)
        if tracked:
            without_lot = tracked.filtered(lambda ml: not ml.lot_id and not ml.lot_name)
            _logger.warning(
                "[msa_mrp_serial_uom] stock.move.line._action_done | total=%s tracked=%s "
                "without_lot=%s detail=%s",
                len(self),
                len(tracked),
                len(without_lot),
                [
                    {
                        'id': ml.id,
                        'move_id': ml.move_id.id,
                        'product': ml.product_id.display_name,
                        'qty': ml.quantity,
                        'uom': ml.product_uom_id.display_name,
                        'qty_product_uom': ml.quantity_product_uom,
                        'lot_id': ml.lot_id.name if ml.lot_id else False,
                        'lot_name': ml.lot_name,
                        'exclude_requiring_lot': ml._exclude_requiring_lot(),
                        'picking_type': ml.move_id.picking_type_id.display_name if ml.move_id.picking_type_id else False,
                        'production_id': ml.move_id.production_id.name if ml.move_id.production_id else False,
                    }
                    for ml in (without_lot[:30] or tracked[:10])
                ],
            )
        return super()._action_done()

    def _exclude_requiring_lot(self):
        result = super()._exclude_requiring_lot()
        if self.product_id.tracking == 'serial' and not result:
            _logger.warning(
                "[msa_mrp_serial_uom] _exclude_requiring_lot=False | sml=%s product=%s "
                "qty=%s uom=%s lot_id=%s lot_name=%s move=%s picking_type=%s",
                self.id,
                self.product_id.display_name,
                self.quantity,
                self.product_uom_id.display_name,
                self.lot_id.name if self.lot_id else False,
                self.lot_name,
                self.move_id.id,
                self.move_id.picking_type_id.display_name if self.move_id.picking_type_id else False,
            )
        return result
