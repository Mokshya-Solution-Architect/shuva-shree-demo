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
    consignment_return_lot_name = fields.Char(
        string='Consignment Return Lot Name',
        copy=False,
        help=(
            'Plain-text lot name for the return lot. '
            'Stored on the order line so the POS can restore pack_lot_ids '
            'from IndexedDB after a page reload before server sync completes.'
        ),
    )

    @api.model
    def _load_pos_data_fields(self, config):
        fields_list = super()._load_pos_data_fields(config)
        for fname in (
            'is_consignment_return',
            'consignment_return_lot_id',
            'consignment_return_lot_name',
        ):
            if fname not in fields_list:
                fields_list.append(fname)
        return fields_list

    @api.model
    def get_existing_lots(self, company_id, config_id, product_id):
        """Extend core lot search to include the consignment return staging location.

        Core ``get_existing_lots`` only looks at ``stock.quant`` records inside the
        POS picking type's source location (warehouse stock).  Return lots live in
        the *Consignment Returns* staging location and are therefore invisible to the
        standard picker.  We run a second quant query for that location and merge
        the results (de-duplicated by lot ID).
        """
        result = super().get_existing_lots(company_id, config_id, product_id)

        pos_config = self.env['pos.config'].browse(config_id)
        if not pos_config.enable_consignment or not pos_config.consignment_return_location_id:
            return result

        return_loc = pos_config.consignment_return_location_id

        # Resolve location IDs via search first (child_of in _read_group domain
        # can be unreliable for leaf locations).  Include the staging location
        # itself plus any internal sub-locations.
        location_ids = self.sudo().env['stock.location'].search([
            ('id', 'child_of', return_loc.id),
            ('usage', '=', 'internal'),
        ]).ids
        if not location_ids:
            location_ids = [return_loc.id]

        quant_domain = [
            '|',
            ('company_id', '=', False),
            ('company_id', '=', company_id),
            ('product_id', '=', product_id),
            ('location_id', 'in', location_ids),
            ('quantity', '>', 0),
            ('lot_id', '!=', False),
        ]

        groups = self.sudo().env['stock.quant']._read_group(
            domain=quant_domain,
            groupby=['lot_id'],
            aggregates=['quantity:sum'],
        )

        existing_ids = {r['id'] for r in result}
        for lot_record, total_quantity in groups:
            if lot_record and lot_record.id not in existing_ids:
                result.append({
                    'id': lot_record.id,
                    'name': lot_record.name,
                    'product_qty': total_quantity,
                })

        return result
