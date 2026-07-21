# -*- coding: utf-8 -*-

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Expose uom_ids (Packagings) and sales_default_packaging_id to POS frontend."""
        fields = super()._load_pos_data_fields(config_id)
        for fname in ('uom_ids', 'sales_default_packaging_id'):
            if fname in self._fields and fname not in fields:
                fields.append(fname)
        return fields
