# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_exchange_return_location_id = fields.Many2one(
        related='pos_config_id.exchange_return_location_id',
        readonly=False,
    )
    pos_exchange_rework_location_id = fields.Many2one(
        related='pos_config_id.exchange_rework_location_id',
        readonly=False,
    )
    pos_exchange_scrap_location_id = fields.Many2one(
        related='pos_config_id.exchange_scrap_location_id',
        readonly=False,
    )
    pos_exchange_stock_location_id = fields.Many2one(
        related='pos_config_id.exchange_stock_location_id',
        readonly=False,
    )
