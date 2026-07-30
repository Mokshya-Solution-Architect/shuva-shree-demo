# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_consignment = fields.Boolean(
        string='Enable Consignment Dispatch',
        default=False,
        help='Shows the Consignment Dispatch and Settle buttons in the POS interface.',
    )
    consignment_location_id = fields.Many2one(
        'stock.location',
        string='Consignment Transit Location',
        check_company=True,
        domain="[('usage', '=', 'transit')]",
        help='Transit location for goods dispatched to supplier-distributors. '
             'Goods move here at dispatch and leave at settlement.',
    )
    consignment_return_location_id = fields.Many2one(
        'stock.location',
        string='Consignment Returns Staging',
        check_company=True,
        domain="[('usage', '=', 'internal')]",
        help='Staging location for loose good returns awaiting resale to the distributor.',
    )

    @api.model
    def _ss_configure_consignment_defaults(self, configs=None):
        """Populate consignment locations from the warehouse for all POS configs."""
        if configs is None:
            configs = self.search([])
        for config in configs:
            warehouse = config.warehouse_id
            if not warehouse:
                continue
            self.env['stock.warehouse']._ss_ensure_consignment_location(warehouse)
            vals = {}
            if not config.consignment_location_id and warehouse.consignment_location_id:
                vals['consignment_location_id'] = warehouse.consignment_location_id.id
            if not config.consignment_return_location_id and warehouse.consignment_return_location_id:
                vals['consignment_return_location_id'] = warehouse.consignment_return_location_id.id
            if vals:
                config.write(vals)
        return True

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id_consignment_location(self):
        if self.warehouse_id:
            self.env['stock.warehouse']._ss_ensure_consignment_location(self.warehouse_id)
            self.consignment_location_id = self.warehouse_id.consignment_location_id
            self.consignment_return_location_id = self.warehouse_id.consignment_return_location_id
