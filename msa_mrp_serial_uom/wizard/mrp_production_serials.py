from odoo import models
from odoo.exceptions import UserError


class MrpProductionSerials(models.TransientModel):
    _inherit = 'mrp.production.serials'

    def action_apply(self):
        self.ensure_one()
        production = self.production_id
        if production.product_tracking == 'lot' and production._msa_is_alt_uom_mo():
            names = [
                n.strip() for n in (self.serial_numbers or '').split('\n') if n.strip()
            ]
            if names:
                expected = int(production.product_uom_id.round(
                    production.product_qty, rounding_method='HALF-UP',
                ))
                if len(names) != expected:
                    raise UserError(self.env._(
                        "Lot count (%(got)s) must equal MO quantity %(expected)s %(uom)s "
                        "(one unique lot per %(uom)s).",
                        got=len(names),
                        expected=expected,
                        uom=production.product_uom_id.display_name,
                    ))
        return super(
            MrpProductionSerials,
            self.with_context(msa_multi_lot_mode=True),
        ).action_apply()
