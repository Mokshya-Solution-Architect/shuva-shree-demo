# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    exchange_return_location_id = fields.Many2one(
        'stock.location',
        string='Exchange Returns Location',
        check_company=True,
        domain="[('usage', '=', 'internal')]",
        help='Quarantine inbound for all POS exchanges before scrap/rework split.',
    )
    exchange_rework_location_id = fields.Many2one(
        'stock.location',
        string='Exchange Rework Location',
        check_company=True,
        domain="[('usage', '=', 'internal')]",
        help='Reusable packaging-damage stock waiting for unbuild/repack. Not sellable from POS.',
    )
    exchange_scrap_location_id = fields.Many2one(
        'stock.location',
        string='Exchange Scrap Location',
        check_company=True,
        domain="[('usage', '=', 'inventory')]",
        help='Expired / unsellable waste from POS exchanges.',
    )
    exchange_stock_location_id = fields.Many2one(
        'stock.location',
        string='Exchange FG Stock Location',
        check_company=True,
        domain="[('usage', '=', 'internal')]",
        help='Sellable finished goods used to issue replacements.',
    )

    @api.model
    def _ss_configure_exchange_defaults(self, configs=None):
        if configs is None:
            configs = self.search([])
        for config in configs:
            warehouse = config.warehouse_id
            if not warehouse:
                continue
            self.env['stock.warehouse']._ss_ensure_exchange_locations(warehouse)
            vals = {}
            if not config.exchange_return_location_id:
                vals['exchange_return_location_id'] = warehouse.exchange_return_location_id.id
            if not config.exchange_rework_location_id:
                vals['exchange_rework_location_id'] = warehouse.exchange_rework_location_id.id
            if not config.exchange_scrap_location_id:
                vals['exchange_scrap_location_id'] = warehouse.exchange_scrap_location_id.id
            if not config.exchange_stock_location_id:
                vals['exchange_stock_location_id'] = warehouse.lot_stock_id.id
            if vals:
                config.write(vals)
        return True

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id_exchange_locations(self):
        if self.warehouse_id:
            self.env['stock.warehouse']._ss_ensure_exchange_locations(self.warehouse_id)
            self.exchange_return_location_id = self.warehouse_id.exchange_return_location_id
            self.exchange_rework_location_id = self.warehouse_id.exchange_rework_location_id
            self.exchange_scrap_location_id = self.warehouse_id.exchange_scrap_location_id
            self.exchange_stock_location_id = self.warehouse_id.lot_stock_id
