# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    consignment_location_id = fields.Many2one(
        'stock.location',
        string='Consignment Transit Location',
        check_company=True,
        help='Transit location for goods dispatched to supplier-distributors until settlement. '
             'Uses usage=transit so stock is not counted as warehouse on-hand.',
    )
    consignment_return_location_id = fields.Many2one(
        'stock.location',
        string='Consignment Returns Staging',
        check_company=True,
        help='Internal staging for loose good returns from consignment settlement. '
             'Returned pieces receive a new lot/serial before resale to the distributor.',
    )

    @api.model
    def _ss_ensure_consignment_location(self, warehouses=None):
        """Create / repair consignment transit + returns staging locations."""
        if warehouses is None:
            warehouses = self.search([])
        Location = self.env['stock.location'].sudo()
        PosConfig = self.env['pos.config'].sudo()
        for warehouse in warehouses:
            view = warehouse.view_location_id
            if not view:
                continue
            company = warehouse.company_id
            vals = {}

            # --- Transit location (usage=transit) ---
            transit = warehouse.consignment_location_id
            if not transit:
                transit = Location.search([
                    ('name', 'in', ('Consignment Transit', 'Consignment In Transit')),
                    ('location_id', 'child_of', view.id),
                ], limit=1, order='id desc')

            if transit and transit.usage == 'internal' and transit.quant_ids:
                # Cannot change usage while stock remains — create a proper transit sibling.
                transit = Location.search([
                    ('name', '=', 'Consignment In Transit'),
                    ('location_id', '=', view.id),
                    ('usage', '=', 'transit'),
                ], limit=1)
                if not transit:
                    transit = Location.create({
                        'name': 'Consignment In Transit',
                        'usage': 'transit',
                        'location_id': view.id,
                        'company_id': company.id,
                    })
            elif transit and transit.usage != 'transit' and not transit.quant_ids:
                transit.write({'usage': 'transit'})
            elif not transit:
                transit = Location.create({
                    'name': 'Consignment Transit',
                    'usage': 'transit',
                    'location_id': view.id,
                    'company_id': company.id,
                })
            vals['consignment_location_id'] = transit.id

            # --- Returns staging (internal) ---
            staging = warehouse.consignment_return_location_id
            if not staging:
                staging = Location.search([
                    ('name', '=', 'Consignment Returns'),
                    ('location_id', 'child_of', view.id),
                    ('usage', '=', 'internal'),
                ], limit=1)
            if not staging:
                staging = Location.create({
                    'name': 'Consignment Returns',
                    'usage': 'internal',
                    'location_id': view.id,
                    'company_id': company.id,
                })
            vals['consignment_return_location_id'] = staging.id

            warehouse.write(vals)

            # Keep POS configs on this warehouse in sync.
            configs = PosConfig.search([('warehouse_id', '=', warehouse.id)])
            for config in configs:
                config.write({
                    'consignment_location_id': transit.id,
                    'consignment_return_location_id': staging.id,
                })
        return True
