# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    exchange_return_location_id = fields.Many2one(
        'stock.location', string='POS Exchange Returns', check_company=True,
    )
    exchange_rework_location_id = fields.Many2one(
        'stock.location', string='POS Exchange Rework', check_company=True,
    )
    exchange_scrap_location_id = fields.Many2one(
        'stock.location', string='POS Exchange Scrap', check_company=True,
    )

    @api.model
    def _ss_ensure_exchange_locations(self, warehouses=None):
        """Create Returns / Rework / Scrap under each warehouse view location."""
        if warehouses is None:
            warehouses = self.search([])
        Location = self.env['stock.location'].sudo()
        for warehouse in warehouses:
            view = warehouse.view_location_id
            if not view:
                continue
            company = warehouse.company_id
            returns = warehouse.exchange_return_location_id or Location.search([
                ('name', '=', 'Returns'),
                ('location_id', '=', view.id),
                ('usage', '=', 'internal'),
            ], limit=1)
            if not returns:
                returns = Location.create({
                    'name': 'Returns',
                    'usage': 'internal',
                    'location_id': view.id,
                    'company_id': company.id,
                })
            rework = warehouse.exchange_rework_location_id or Location.search([
                ('name', '=', 'Rework'),
                ('location_id', '=', view.id),
                ('usage', '=', 'internal'),
            ], limit=1)
            if not rework:
                rework = Location.create({
                    'name': 'Rework',
                    'usage': 'internal',
                    'location_id': view.id,
                    'company_id': company.id,
                })
            scrap = warehouse.exchange_scrap_location_id or Location.search([
                ('name', '=', 'Scrap'),
                ('location_id', '=', view.id),
                ('usage', '=', 'inventory'),
            ], limit=1)
            if not scrap:
                scrap = Location.create({
                    'name': 'Scrap',
                    'usage': 'inventory',
                    'location_id': view.id,
                    'company_id': company.id,
                })
            warehouse.write({
                'exchange_return_location_id': returns.id,
                'exchange_rework_location_id': rework.id,
                'exchange_scrap_location_id': scrap.id,
            })
        return True
