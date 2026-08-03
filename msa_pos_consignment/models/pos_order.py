# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_consignment_settlement = fields.Boolean(
        string='Consignment Settlement',
        default=False,
        copy=False,
        help='Stock for sold qty was moved during pos.consignment.action_settle.',
    )
    is_consignment_resale = fields.Boolean(
        string='Consignment Return Resale',
        default=False,
        copy=False,
        help='Reselling loose good-return stock to the distributor.',
    )
    consignment_id = fields.Many2one(
        'pos.consignment',
        string='Consignment',
        copy=False,
        index=True,
        ondelete='set null',
    )

    def _create_order_picking(self):
        self.ensure_one()
        if self.is_consignment_settlement:
            return
        return_lines = self.lines.filtered('is_consignment_return')
        other_lines = self.lines - return_lines
        if return_lines:
            self._create_consignment_return_resale_pickings(return_lines)
        if other_lines:
            if return_lines:
                self._create_order_picking_for_lines(other_lines)
            else:
                super()._create_order_picking()

    def _create_order_picking_for_lines(self, lines):
        """Core POS picking logic for a subset of lines (resale + fresh stock)."""
        self.ensure_one()
        if self.shipping_date:
            lines.sudo()._launch_stock_rule_from_pos_order_lines()
        elif self._should_create_picking_real_time():
            picking_type = self.config_id.picking_type_id
            if self.partner_id.property_stock_customer:
                destination_id = self.partner_id.property_stock_customer.id
            elif not picking_type or not picking_type.default_location_dest_id:
                destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
            else:
                destination_id = picking_type.default_location_dest_id.id
            pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(
                destination_id, lines, picking_type, self.partner_id,
            )
            all_pickings = pickings | pickings.backorder_ids
            all_pickings.write({
                'pos_session_id': self.session_id.id,
                'pos_order_id': self.id,
                'origin': self.name,
            })

    def _create_consignment_return_resale_pickings(self, return_lines):
        self.ensure_one()
        config = self.config_id
        staging = config.consignment_return_location_id
        if not staging:
            raise UserError(_(
                'Consignment Returns Staging is not configured on POS %s.',
                config.display_name,
            ))
        if self.partner_id.property_stock_customer:
            customer_loc = self.partner_id.property_stock_customer
        else:
            customer_loc = self.env['stock.warehouse']._get_partner_locations()[0]
        picking_type = config.picking_type_id
        consignment = self.consignment_id
        if not consignment:
            consignment = self.env['pos.consignment']
        for line in return_lines:
            lot = line.consignment_return_lot_id
            if line.product_id.tracking != 'none' and not lot:
                raise UserError(_(
                    'Consignment return line for %s is missing a return lot.',
                    line.product_id.display_name,
                ))
            qty = abs(line.qty)
            uom = line.product_uom_id or line.product_id.uom_id
            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': staging.id,
                'location_dest_id': customer_loc.id,
                'partner_id': self.partner_id.id,
                'origin': self.name,
                'company_id': self.company_id.id,
                'pos_session_id': self.session_id.id,
                'pos_order_id': self.id,
                'move_type': 'direct',
            })
            consignment._create_stock_move(
                picking=picking,
                product=line.product_id,
                qty=qty,
                uom=uom,
                lot=lot,
                src=staging,
                dest=customer_loc,
                require_stock=True,
            )
            picking.with_context(skip_sms=True, cancel_backorder=True)._action_done()

    def _process_saved_order(self, draft):
        result = super()._process_saved_order(draft)
        if not draft and self.is_consignment_settlement and self.consignment_id:
            self.consignment_id.sudo().write({'settlement_order_id': self.id})
        return result
