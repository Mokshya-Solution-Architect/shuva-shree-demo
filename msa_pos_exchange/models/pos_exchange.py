# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tools import float_compare, float_is_zero, float_round


class PosExchange(models.Model):
    _name = 'pos.exchange'
    _description = 'POS Product Exchange'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )
    session_id = fields.Many2one(
        'pos.session',
        string='POS Session',
        required=True,
        ondelete='restrict',
        index=True,
        check_company=True,
    )
    config_id = fields.Many2one(
        related='session_id.config_id',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related='session_id.company_id',
        store=True,
        readonly=True,
        index=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Cashier',
        default=lambda self: self.env.user,
        required=True,
        ondelete='restrict',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        ondelete='set null',
        check_company=True,
    )
    note = fields.Text(string='Note')
    line_ids = fields.One2many('pos.exchange.line', 'exchange_id', string='Lines', copy=True)
    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order',
        copy=False,
        readonly=True,
        ondelete='set null',
    )
    picking_ids = fields.Many2many(
        'stock.picking',
        'pos_exchange_picking_rel',
        'exchange_id',
        'picking_id',
        string='Transfers',
        copy=False,
        readonly=True,
    )
    scrap_ids = fields.Many2many(
        'stock.scrap',
        'pos_exchange_scrap_rel',
        'exchange_id',
        'scrap_id',
        string='Scraps',
        copy=False,
        readonly=True,
    )
    date_done = fields.Datetime(string='Confirmed On', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('pos.exchange') or _('New')
        return super().create(vals_list)

    def action_cancel(self):
        for exchange in self:
            if exchange.state == 'done':
                raise UserError(_('You cannot cancel a confirmed exchange.'))
            exchange.state = 'cancel'
        return True

    @api.model
    def _find_lot_by_name(self, lot_name, company, product=None):
        """Resolve lot/SN with company scope. Prefer product match when provided."""
        lot_name = (lot_name or '').strip()
        if not lot_name:
            return self.env['stock.lot']
        domain = [
            ('name', '=', lot_name),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', company.id),
        ]
        if product:
            domain = [('product_id', '=', product.id)] + domain
        lots = self.env['stock.lot'].search(domain, limit=5)
        if not lots:
            return self.env['stock.lot']
        if not product and len(lots) > 1:
            products = lots.mapped('product_id')
            if len(products) > 1:
                raise UserError(_(
                    'Lot / Serial "%(lot)s" matches multiple products (%(products)s). '
                    'Scan a unique barcode or start from the original order line.',
                    lot=lot_name,
                    products=', '.join(products.mapped('display_name')),
                ))
        return lots[:1]

    @api.model
    def lookup_lot_for_pos(self, lot_name, config_id=False, role='origin'):
        """Resolve a scanned lot/SN for the POS exchange wizard.

        :param role: 'origin' (returned) or 'replacement' (must be in FG).
        """
        lot_name = (lot_name or '').strip()
        if not lot_name:
            raise UserError(_('Please scan or enter a lot / serial number.'))

        config = self.env['pos.config']
        if config_id:
            config = self.env['pos.config'].search([('id', '=', int(config_id))], limit=1)
        if not config:
            raise UserError(_('POS configuration not found.'))

        self.env['pos.config']._ss_configure_exchange_defaults(config)
        company = config.company_id
        lot = self._find_lot_by_name(lot_name, company)
        if not lot:
            raise UserError(_('Lot / Serial "%s" was not found.', lot_name))

        product = lot.product_id
        origin_line = self._find_origin_order_line(lot, company)
        stock_loc = config.exchange_stock_location_id
        available_fg = 0.0
        if stock_loc and product.is_storable:
            available_fg = self.env['stock.quant']._get_available_quantity(
                product, stock_loc, lot_id=lot, strict=True,
            )

        if role == 'replacement':
            if product.tracking != 'none' and float_compare(
                available_fg, 0.0, precision_rounding=product.uom_id.rounding
            ) <= 0:
                raise UserError(_(
                    'Replacement %(lot)s has no available quantity in %(loc)s.',
                    lot=lot.name,
                    loc=stock_loc.display_name if stock_loc else _('Finished Goods'),
                ))

        return {
            'lot_id': lot.id,
            'lot_name': lot.name,
            'product_id': product.id,
            'product_name': product.display_name,
            'tracking': product.tracking,
            'uom_id': product.uom_id.id,
            'uom_name': product.uom_id.display_name,
            'origin_order_line_id': origin_line.id if origin_line else False,
            'origin_order_name': origin_line.order_id.pos_reference if origin_line else False,
            'available_fg_qty': available_fg,
            'default_qty': 1.0,
            'suggest_expired': bool(
                'expiration_date' in lot._fields
                and lot.expiration_date
                and lot.expiration_date < fields.Datetime.now()
            ),
        }

    @api.model
    def create_from_pos(self, vals):
        """Create and confirm an exchange from the POS UI."""
        session = self.env['pos.session'].search([
            ('id', '=', int(vals.get('session_id') or 0)),
            ('state', '=', 'opened'),
        ], limit=1)
        if not session:
            raise UserError(_('You need an opened POS session to confirm an exchange.'))

        config = session.config_id
        self.env['pos.config']._ss_configure_exchange_defaults(config)
        company = session.company_id

        origin_lot_name = (vals.get('origin_lot_name') or '').strip()
        if not origin_lot_name:
            raise UserError(_('Please scan the original lot / serial number.'))
        origin_lot = self._find_lot_by_name(origin_lot_name, company)
        if not origin_lot:
            raise UserError(_('Lot / Serial "%s" was not found.', origin_lot_name))

        product = origin_lot.product_id
        reason = vals.get('reason')
        if reason not in ('expired', 'packaging_damage'):
            raise UserError(_('Invalid exchange reason.'))

        returned_qty = float(vals.get('returned_qty') or 0.0)
        reusable_qty = float(vals.get('reusable_qty') or 0.0)
        if reason == 'expired':
            reusable_qty = 0.0
        if product.tracking == 'serial':
            returned_qty = 1.0
            reusable_qty = 0.0 if reason == 'expired' else 1.0

        replacement_lot = self.env['stock.lot']
        replacement_lot_name = (vals.get('replacement_lot_name') or '').strip()
        if product.tracking != 'none':
            if not replacement_lot_name:
                raise UserError(_('Please scan the replacement lot / serial number.'))
            if replacement_lot_name == origin_lot_name:
                raise UserError(_('Replacement lot / serial must be different from the returned one.'))
            # Never invent lots — must already exist and be in FG
            replacement_lot = self._find_lot_by_name(replacement_lot_name, company, product=product)
            if not replacement_lot:
                raise UserError(_(
                    'Replacement lot / serial "%s" was not found for this product. '
                    'Scan a lot that already exists in Finished Goods.',
                    replacement_lot_name,
                ))
            stock_loc = config.exchange_stock_location_id
            available = self.env['stock.quant']._get_available_quantity(
                product, stock_loc, lot_id=replacement_lot, strict=True,
            )
            if float_compare(available, returned_qty, precision_rounding=product.uom_id.rounding) < 0:
                raise UserError(_(
                    'Only %(available)s %(uom)s of %(lot)s available in %(loc)s (need %(need)s).',
                    available=available,
                    uom=product.uom_id.display_name,
                    lot=replacement_lot.name,
                    loc=stock_loc.display_name,
                    need=returned_qty,
                ))

        origin_line = self.env['pos.order.line']
        if vals.get('origin_order_line_id'):
            origin_line = self.env['pos.order.line'].search([
                ('id', '=', int(vals['origin_order_line_id'])),
            ], limit=1)
        if not origin_line:
            origin_line = self._find_origin_order_line(origin_lot, company)

        partner = self.env['res.partner']
        if vals.get('partner_id'):
            partner = self.env['res.partner'].search([('id', '=', int(vals['partner_id']))], limit=1)
        elif origin_line:
            partner = origin_line.order_id.partner_id

        exchange = self.create({
            'session_id': session.id,
            'user_id': self.env.user.id,
            'partner_id': partner.id if partner else False,
            'note': vals.get('note') or False,
            'line_ids': [Command.create({
                'product_id': product.id,
                'reason': reason,
                'returned_qty': returned_qty,
                'reusable_qty': reusable_qty,
                'origin_lot_id': origin_lot.id,
                'replacement_lot_id': replacement_lot.id if replacement_lot else False,
                'origin_order_line_id': origin_line.id if origin_line else False,
                'product_uom_id': product.uom_id.id,
            })],
        })
        exchange.action_confirm()
        return {
            'exchange_id': exchange.id,
            'exchange_name': exchange.name,
            'pos_order_id': exchange.pos_order_id.id,
            'pos_reference': exchange.pos_order_id.pos_reference,
        }

    @api.model
    def _find_origin_order_line(self, lot, company=None):
        """Find the most recent non-exchange sale line that used this lot/SN."""
        company = company or self.env.company
        packs = self.env['pos.pack.operation.lot'].search([
            ('lot_name', '=', lot.name),
            ('pos_order_line_id.product_id', '=', lot.product_id.id),
            ('pos_order_line_id.order_id.company_id', '=', company.id),
            ('pos_order_line_id.order_id.is_exchange', '=', False),
            ('pos_order_line_id.order_id.state', 'in', ('paid', 'done', 'invoiced')),
        ], order='id desc', limit=50)
        for pack in packs:
            line = pack.pos_order_line_id
            if not line or float_compare(line.qty, 0.0, precision_rounding=line.product_uom_id.rounding) <= 0:
                continue
            # Remaining qty after prior *native* refunds only (exchanges no longer inflate refunded_qty)
            remaining = line.qty - line.refunded_qty
            if float_compare(remaining, 0.0, precision_rounding=line.product_uom_id.rounding) <= 0:
                continue
            return line
        return self.env['pos.order.line']

    def action_confirm(self):
        for exchange in self:
            if exchange.state != 'draft':
                raise UserError(_('Only draft exchanges can be confirmed.'))
            if not exchange.line_ids:
                raise UserError(_('Add at least one exchange line.'))
            # Atomic: scrap/pickings roll back together on any failure
            with self.env.cr.savepoint():
                exchange._check_locations()
                pickings = self.env['stock.picking']
                scraps = self.env['stock.scrap']
                for line in exchange.line_ids:
                    line._validate_qties()
                    pickings |= exchange._create_receive_picking(line)
                    if not float_is_zero(line.scrap_qty, precision_rounding=line.product_uom_id.rounding):
                        scraps |= exchange._create_scrap(line)
                    if not float_is_zero(line.reusable_qty, precision_rounding=line.product_uom_id.rounding):
                        pickings |= exchange._create_rework_picking(line)
                    pickings |= exchange._create_replacement_picking(line)
                order = exchange._create_zero_pos_order(pickings)
                exchange.write({
                    'state': 'done',
                    'date_done': fields.Datetime.now(),
                    'picking_ids': [Command.set(pickings.ids)],
                    'scrap_ids': [Command.set(scraps.ids)],
                    'pos_order_id': order.id,
                })
                order.write({'exchange_id': exchange.id})
        return True

    def _check_locations(self):
        self.ensure_one()
        config = self.config_id
        missing = []
        if not config.exchange_return_location_id:
            missing.append(_('Returns'))
        if not config.exchange_rework_location_id:
            missing.append(_('Rework'))
        if not config.exchange_scrap_location_id:
            missing.append(_('Scrap'))
        if not config.exchange_stock_location_id:
            missing.append(_('Finished Goods'))
        if missing:
            raise UserError(_(
                'Configure exchange locations on POS %s: %s',
                config.display_name,
                ', '.join(missing),
            ))

    def _customer_location(self):
        self.ensure_one()
        partner = self.partner_id
        if partner and partner.property_stock_customer:
            return partner.property_stock_customer
        return self.env['stock.warehouse']._get_partner_locations()[0]

    def _create_receive_picking(self, line):
        """Customer → Returns for full returned qty with origin lot."""
        self.ensure_one()
        config = self.config_id
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'customer_returns'),
            ('warehouse_id', '=', config.warehouse_id.id),
        ], limit=1) or config.picking_type_id.return_picking_type_id or config.picking_type_id
        return self._create_done_picking(
            picking_type=picking_type,
            location_id=self._customer_location(),
            location_dest_id=config.exchange_return_location_id,
            product=line.product_id,
            qty=line.returned_qty,
            uom=line.product_uom_id,
            lot=line.origin_lot_id,
            origin=self.name,
            partner=self.partner_id,
            require_stock=False,  # customer locations are not reliably quantized
        )

    def _create_rework_picking(self, line):
        """Returns → Rework for reusable qty (must be in Returns after receive)."""
        self.ensure_one()
        config = self.config_id
        picking_type = config.warehouse_id.int_type_id or self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', config.warehouse_id.id),
        ], limit=1)
        return self._create_done_picking(
            picking_type=picking_type,
            location_id=config.exchange_return_location_id,
            location_dest_id=config.exchange_rework_location_id,
            product=line.product_id,
            qty=line.reusable_qty,
            uom=line.product_uom_id,
            lot=line.origin_lot_id,
            origin=self.name,
            partner=self.partner_id,
            require_stock=True,
        )

    def _create_replacement_picking(self, line):
        """FG Stock → Customer for full replacement qty (must be available in FG)."""
        self.ensure_one()
        config = self.config_id
        return self._create_done_picking(
            picking_type=config.picking_type_id,
            location_id=config.exchange_stock_location_id,
            location_dest_id=self._customer_location(),
            product=line.product_id,
            qty=line.returned_qty,
            uom=line.product_uom_id,
            lot=line.replacement_lot_id,
            origin=self.name,
            partner=self.partner_id,
            require_stock=True,
        )

    def _create_scrap(self, line):
        self.ensure_one()
        config = self.config_id
        scrap = self.env['stock.scrap'].create({
            'product_id': line.product_id.id,
            'product_uom_id': line.product_uom_id.id,
            'scrap_qty': line.scrap_qty,
            'lot_id': line.origin_lot_id.id if line.origin_lot_id else False,
            'location_id': config.exchange_return_location_id.id,
            'scrap_location_id': config.exchange_scrap_location_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
        })
        if not scrap.check_available_qty():
            raise UserError(_(
                'Insufficient quantity of %(product)s%(lot)s in %(loc)s to scrap %(qty)s.',
                product=line.product_id.display_name,
                lot=(' (%s)' % line.origin_lot_id.name) if line.origin_lot_id else '',
                loc=config.exchange_return_location_id.display_name,
                qty=line.scrap_qty,
            ))
        scrap.do_scrap()
        return scrap

    def _create_done_picking(
        self, picking_type, location_id, location_dest_id, product, qty, uom, lot,
        origin, partner, require_stock=False,
    ):
        self.ensure_one()
        if float_is_zero(qty, precision_rounding=uom.rounding):
            return self.env['stock.picking']
        if not picking_type:
            raise UserError(_('No operation type configured for this exchange stock move.'))

        if require_stock and product.is_storable:
            available = self.env['stock.quant']._get_available_quantity(
                product, location_id, lot_id=lot if lot else None, strict=bool(lot),
            )
            if float_compare(available, qty, precision_rounding=uom.rounding) < 0:
                raise UserError(_(
                    'Not enough %(product)s%(lot)s in %(loc)s: available %(available)s, need %(need)s.',
                    product=product.display_name,
                    lot=(' [%s]' % lot.name) if lot else '',
                    loc=location_id.display_name,
                    available=available,
                    need=qty,
                ))

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'partner_id': partner.id if partner else False,
            'origin': origin,
            'company_id': self.company_id.id,
            'pos_session_id': self.session_id.id,
            'move_type': 'direct',
        })
        move = self.env['stock.move'].create({
            'origin': origin,
            'product_id': product.id,
            'product_uom': uom.id,
            'product_uom_qty': qty,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'picking_id': picking.id,
            'picking_type_id': picking_type.id,
            'company_id': self.company_id.id,
        })
        move._action_confirm()
        move._action_assign()
        self._set_move_lines(move, product, qty, uom, lot, location_id, location_dest_id, picking, require_stock)
        move.picked = True
        picking.with_context(skip_sms=True, cancel_backorder=True)._action_done()
        if picking.state != 'done':
            raise UserError(_(
                'Could not complete stock transfer %(picking)s for exchange %(exchange)s.',
                picking=picking.name or picking.id,
                exchange=self.name,
            ))
        return picking

    def _set_move_lines(self, move, product, qty, uom, lot, location_id, location_dest_id, picking, require_stock):
        """Build move lines, preferring real quants when stock is required (core POS style)."""
        move.move_line_ids.unlink()
        Quant = self.env['stock.quant']
        ml_vals_list = []

        if lot and require_stock and product.is_storable:
            quants = Quant.search([
                ('product_id', '=', product.id),
                ('lot_id', '=', lot.id),
                ('quantity', '>', 0.0),
                ('location_id', 'child_of', location_id.id),
            ], order='id desc')
            qty_left = qty
            for quant in quants:
                if float_compare(qty_left, 0.0, precision_rounding=uom.rounding) <= 0:
                    break
                qty_chg = min(qty_left, quant.quantity)
                vals = dict(move._prepare_move_line_vals(qty_chg))
                vals['quant_id'] = quant.id
                ml_vals_list.append(vals)
                qty_left -= qty_chg
            if float_compare(qty_left, 0.0, precision_rounding=uom.rounding) > 0:
                raise UserError(_(
                    'Could not reserve %(qty)s of %(lot)s in %(loc)s.',
                    qty=qty,
                    lot=lot.name,
                    loc=location_id.display_name,
                ))
        else:
            vals = {
                'move_id': move.id,
                'product_id': product.id,
                'product_uom_id': uom.id,
                'quantity': qty,
                'location_id': location_id.id,
                'location_dest_id': location_dest_id.id,
                'picking_id': picking.id,
                'company_id': self.company_id.id,
            }
            if lot:
                vals['lot_id'] = lot.id
            ml_vals_list.append(vals)

        self.env['stock.move.line'].create(ml_vals_list)

    def _create_zero_pos_order(self, pickings):
        """Audit POS order: -returned + replacement at price 0. No refunded_orderline_id."""
        self.ensure_one()
        session = self.session_id
        line_commands = []
        for line in self.line_ids:
            return_pack = []
            replace_pack = []
            if line.origin_lot_id:
                return_pack = [Command.create({'lot_name': line.origin_lot_id.name})]
            if line.replacement_lot_id:
                replace_pack = [Command.create({'lot_name': line.replacement_lot_id.name})]
            reason_label = dict(line._fields['reason'].selection).get(line.reason, line.reason)
            # Intentionally NOT setting refunded_orderline_id — that field drives native
            # refunded_qty and would block cash refunds / mis-report exchanges as refunds.
            line_commands.append(Command.create({
                'product_id': line.product_id.id,
                'qty': -line.returned_qty,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'price_subtotal_incl': 0.0,
                'discount': 0.0,
                'full_product_name': _(
                    '%(product)s (Exchange Return — %(reason)s)',
                    product=line.product_id.display_name,
                    reason=reason_label,
                ),
                'pack_lot_ids': return_pack,
                'tax_ids': [Command.clear()],
                'customer_note': _('Origin SO line: %s', line.origin_order_line_id.order_id.pos_reference)
                if line.origin_order_line_id else False,
            }))
            line_commands.append(Command.create({
                'product_id': line.product_id.id,
                'qty': line.returned_qty,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'price_subtotal_incl': 0.0,
                'discount': 0.0,
                'full_product_name': _(
                    '%(product)s (Exchange Replacement)',
                    product=line.product_id.display_name,
                ),
                'pack_lot_ids': replace_pack,
                'tax_ids': [Command.clear()],
            }))
        order = self.env['pos.order'].create({
            'session_id': session.id,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'user_id': self.user_id.id,
            'amount_tax': 0.0,
            'amount_total': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'is_exchange': True,
            'general_customer_note': self.note or _('POS Exchange %s', self.name),
            'lines': line_commands,
        })
        if pickings:
            pickings.write({
                'pos_order_id': order.id,
                'pos_session_id': session.id,
            })
        order.action_pos_order_paid()
        if hasattr(order, '_compute_total_cost_in_real_time'):
            order._compute_total_cost_in_real_time()
        return order


class PosExchangeLine(models.Model):
    _name = 'pos.exchange.line'
    _description = 'POS Product Exchange Line'
    _check_company_auto = True

    exchange_id = fields.Many2one(
        'pos.exchange',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="[('type', '=', 'consu')]",
        ondelete='restrict',
        check_company=True,
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit',
        required=True,
        ondelete='restrict',
    )
    reason = fields.Selection(
        [
            ('expired', 'Expired'),
            ('packaging_damage', 'Packaging damage'),
        ],
        string='Reason',
        required=True,
        default='packaging_damage',
    )
    returned_qty = fields.Float(string='Returned Qty', digits='Product Unit', required=True, default=1.0)
    reusable_qty = fields.Float(string='Reusable Qty', digits='Product Unit', default=0.0)
    scrap_qty = fields.Float(
        string='Scrap Qty',
        digits='Product Unit',
        compute='_compute_scrap_qty',
        store=True,
    )
    origin_lot_id = fields.Many2one(
        'stock.lot',
        string='Returned Lot/SN',
        domain="[('product_id', '=', product_id)]",
        check_company=True,
        ondelete='restrict',
    )
    replacement_lot_id = fields.Many2one(
        'stock.lot',
        string='Replacement Lot/SN',
        domain="[('product_id', '=', product_id)]",
        check_company=True,
        ondelete='restrict',
    )
    origin_order_line_id = fields.Many2one(
        'pos.order.line',
        string='Original Order Line',
        ondelete='set null',
        help='Audit link to the original sale line (does not affect refunded_qty).',
    )
    company_id = fields.Many2one(related='exchange_id.company_id', store=True)

    _reusable_le_returned = models.Constraint(
        'CHECK(reusable_qty <= returned_qty)',
        'Reusable quantity cannot exceed returned quantity.',
    )

    @api.depends('returned_qty', 'reusable_qty', 'product_uom_id')
    def _compute_scrap_qty(self):
        for line in self:
            rounding = line.product_uom_id.rounding if line.product_uom_id else 0.01
            line.scrap_qty = float_round(line.returned_qty - line.reusable_qty, precision_rounding=rounding)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id

    @api.onchange('reason')
    def _onchange_reason(self):
        if self.reason == 'expired':
            self.reusable_qty = 0.0
        elif self.reason == 'packaging_damage' and float_is_zero(
            self.reusable_qty, precision_rounding=self.product_uom_id.rounding or 0.01
        ):
            self.reusable_qty = self.returned_qty

    def _validate_qties(self):
        self.ensure_one()
        rounding = self.product_uom_id.rounding
        if float_compare(self.returned_qty, 0.0, precision_rounding=rounding) <= 0:
            raise ValidationError(_('Returned quantity must be positive.'))
        if float_compare(self.reusable_qty, 0.0, precision_rounding=rounding) < 0:
            raise ValidationError(_('Reusable quantity cannot be negative.'))
        if float_compare(self.reusable_qty, self.returned_qty, precision_rounding=rounding) > 0:
            raise ValidationError(_('Reusable quantity cannot exceed returned quantity.'))
        if self.reason == 'expired' and not float_is_zero(self.reusable_qty, precision_rounding=rounding):
            raise ValidationError(_('Expired exchanges cannot have reusable quantity.'))
        if self.product_id.tracking == 'serial':
            if float_compare(self.returned_qty, 1.0, precision_rounding=rounding) != 0:
                raise ValidationError(_('Serial-tracked products must be exchanged one unit at a time.'))
            if not self.origin_lot_id or not self.replacement_lot_id:
                raise ValidationError(_('Serial-tracked products require both returned and replacement serials.'))
        elif self.product_id.tracking == 'lot':
            if not self.origin_lot_id:
                raise ValidationError(_('Please set the returned lot.'))
            if not self.replacement_lot_id:
                raise ValidationError(_('Please set the replacement lot.'))
