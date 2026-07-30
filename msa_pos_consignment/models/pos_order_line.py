# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    is_consignment_return = fields.Boolean(
        string='Consignment Return Resale',
        default=False,
        copy=False,
        help='Line sells loose good-return stock from the consignment returns staging location.',
    )
    consignment_return_lot_id = fields.Many2one(
        'stock.lot',
        string='Consignment Return Lot',
        copy=False,
        ondelete='restrict',
    )

    @api.model
    def _load_pos_data_fields(self, config):
        fields_list = super()._load_pos_data_fields(config)
        for fname in ('is_consignment_return', 'consignment_return_lot_id'):
            if fname not in fields_list:
                fields_list.append(fname)
        return fields_list
