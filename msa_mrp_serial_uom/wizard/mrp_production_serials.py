import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MrpProductionSerials(models.TransientModel):
    _inherit = 'mrp.production.serials'

    def action_generate_serial_numbers(self):
        self.ensure_one()
        _logger.warning(
            "[msa_mrp_serial_uom] wizard generate | MO=%s lot_name=%s lot_quantity=%s tracking=%s",
            self.production_id.name,
            self.lot_name,
            self.lot_quantity,
            self.production_id.product_tracking,
        )
        return super().action_generate_serial_numbers()

    def action_apply(self):
        self.ensure_one()
        production = self.production_id
        names = [
            n.strip() for n in (self.serial_numbers or '').split('\n') if n.strip()
        ]
        _logger.warning(
            "[msa_mrp_serial_uom] wizard action_apply | MO=%s tracking=%s qty=%s uom=%s "
            "names_count=%s",
            production.name,
            production.product_tracking,
            production.product_qty,
            production.product_uom_id.display_name,
            len(names),
        )
        if (
            production.product_tracking == 'lot'
            and production._msa_is_alt_uom_mo()
            and names
        ):
            expected = int(production.product_uom_id.round(
                production.product_qty, rounding_method='HALF-UP',
            ))
            if len(names) != expected:
                from odoo.exceptions import UserError
                raise UserError(self.env._(
                    "Lot count (%(got)s) must equal MO quantity %(expected)s %(uom)s "
                    "(one unique lot per %(uom)s).",
                    got=len(names),
                    expected=expected,
                    uom=production.product_uom_id.display_name,
                ))
        return super(MrpProductionSerials, self.with_context(msa_multi_lot_mode=True)).action_apply()
