# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_enable_consignment = fields.Boolean(
        related='pos_config_id.enable_consignment',
        readonly=False,
    )
    pos_consignment_location_id = fields.Many2one(
        related='pos_config_id.consignment_location_id',
        readonly=False,
    )
    pos_consignment_return_location_id = fields.Many2one(
        related='pos_config_id.consignment_return_location_id',
        readonly=False,
    )
