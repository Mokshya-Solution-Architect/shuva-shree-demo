# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools import float_compare, float_is_zero, float_round


class PosConsignment(models.Model):
    _name = 'pos.consignment'
    _description = 'POS Consignment Dispatch'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pos.load.mixin']
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
            ('dispatched', 'Dispatched'),
            ('settled', 'Settled'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Distributor / Supplier',
        required=True,
        ondelete='restrict',
        check_company=True,
        tracking=True,
    )
    dispatch_session_id = fields.Many2one(
        'pos.session',
        string='Dispatch Session',
        ondelete='restrict',
        index=True,
        check_company=True,
        readonly=True,
    )
    settlement_session_id = fields.Many2one(
        'pos.session',
        string='Settlement Session',
        ondelete='restrict',
        index=True,
        check_company=True,
        readonly=True,
    )
    config_id = fields.Many2one(
        'pos.config',
        string='POS',
        related='dispatch_session_id.config_id',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        related='dispatch_session_id.company_id',
        store=True,
        readonly=True,
        index=True,
    )
    dispatch_date = fields.Datetime(string='Dispatch Date', readonly=True, copy=False)
    settlement_date = fields.Datetime(string='Settlement Date', readonly=True, copy=False)
    line_ids = fields.One2many(
        'pos.consignment.line',
        'consignment_id',
        string='Dispatch Lines',
        copy=True,
    )
    dispatch_picking_id = fields.Many2one(
        'stock.picking',
        string='Dispatch Transfer',
        copy=False,
        readonly=True,
        ondelete='set null',
    )
    return_picking_ids = fields.Many2many(
        'stock.picking',
        'pos_consignment_return_picking_rel',
        'consignment_id',
        'picking_id',
        string='Return Transfers',
        copy=False,
        readonly=True,
    )
    sold_picking_id = fields.Many2one(
        'stock.picking',
        string='Sold Transfer',
        copy=False,
        readonly=True,
        ondelete='set null',
    )
    settlement_order_id = fields.Many2one(
        'pos.order',
        string='Settlement POS Order',
        copy=False,
        readonly=True,
        ondelete='set null',
    )
    note = fields.Text(string='Internal Note')
    amount_dispatched = fields.Monetary(
        string='Amount Dispatched',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    amount_settled = fields.Monetary(
        string='Amount Settled',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='dispatch_session_id.currency_id',
        store=True,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('pos.consignment') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.qty_dispatched', 'line_ids.price_unit', 'line_ids.qty_sold', 'line_ids.price_unit_base')
    def _compute_amounts(self):
        for rec in self:
            dispatched = 0.0
            settled = 0.0
            for line in rec.line_ids:
                dispatched += line.qty_dispatched * line.price_unit
                settled += line.qty_sold * line.price_unit_base
            rec.amount_dispatched = dispatched
            rec.amount_settled = settled

    def action_cancel(self):
        for rec in self:
            if rec.state not in ('draft', 'dispatched'):
                raise UserError(_('Only Draft or Dispatched consignments can be cancelled.'))
            if rec.state == 'dispatched' and rec.dispatch_picking_id:
                raise UserError(_(
                    'Consignment %s has an active dispatch transfer. '
                    'Process a full return settlement before cancelling.',
                    rec.name,
                ))
            rec.state = 'cancelled'
        return True

    # -------------------------------------------------------------------------
    # POS RPC Methods (called from the OWL frontend)
    # -------------------------------------------------------------------------

    @api.model
    def _resolve_dispatch_lot(self, line_data, product, company):
        """Resolve stock.lot from lot_id or lot_name sent by the POS dispatch basket."""
        Lot = self.env['stock.lot']
        if line_data.get('lot_id'):
            lot = Lot.search([('id', '=', int(line_data['lot_id']))], limit=1)
            if lot:
                return lot
        lot_name = (line_data.get('lot_name') or '').strip()
        if not lot_name:
            return Lot
        return Lot.search([
            ('name', '=', lot_name),
            ('product_id', '=', product.id),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', company.id),
        ], limit=1)

    @api.model
    def get_open_for_partner(self, partner_id, config_id):
        """Return all dispatched consignments for a partner on this POS config."""
        partner = self.env['res.partner'].search([('id', '=', int(partner_id))], limit=1)
        config = self.env['pos.config'].search([('id', '=', int(config_id))], limit=1)
        if not partner or not config:
            return []
        records = self.search([
            ('state', '=', 'dispatched'),
            ('config_id', '=', config.id),
            ('partner_id', '=', partner.id),
        ])
        result = []
        for rec in records:
            result.append({
                'id': rec.id,
                'name': rec.name,
                'dispatch_date': fields.Datetime.to_string(rec.dispatch_date),
                'amount_dispatched': rec.amount_dispatched,
                'lines': [line._pos_line_payload() for line in rec.line_ids],
            })
        return result

    @api.model
    def action_dispatch(self, vals):
        """Create and confirm a consignment dispatch from the POS UI.

        vals = {
            'session_id': int,
            'partner_id': int,
            'lines': [
                {
                    'product_id': int,
                    'lot_id': int or False,
                    'qty': float,
                    'price_unit': float,
                    'uom_id': int,
                }
            ],
            'note': str or False,
        }
        Returns: {'consignment_id': int, 'consignment_name': str, 'picking_name': str}
        """
        session = self.env['pos.session'].search([
            ('id', '=', int(vals.get('session_id') or 0)),
            ('state', '=', 'opened'),
        ], limit=1)
        if not session:
            raise UserError(_('You need an open POS session to create a consignment dispatch.'))

        config = session.config_id
        if not config.enable_consignment:
            raise UserError(_('Consignment dispatch is not enabled on this POS.'))

        partner = self.env['res.partner'].search([
            ('id', '=', int(vals.get('partner_id') or 0)),
        ], limit=1)
        if not partner:
            raise UserError(_('Please select a distributor before dispatching.'))

        lines_data = vals.get('lines') or []
        if not lines_data:
            raise UserError(_('Add at least one product line to the dispatch.'))

        line_commands = []
        company = session.company_id
        for ld in lines_data:
            product = self.env['product.product'].search([
                ('id', '=', int(ld.get('product_id') or 0)),
            ], limit=1)
            if not product:
                raise UserError(_('Product not found for line data: %s', ld))
            qty = float(ld.get('qty') or 0.0)
            if float_compare(qty, 0.0, precision_rounding=product.uom_id.rounding) <= 0:
                raise UserError(_(
                    'Dispatch quantity for %s must be positive.', product.display_name
                ))
            lot = self._resolve_dispatch_lot(ld, product, company)
            if product.tracking != 'none' and not lot:
                raise UserError(_(
                    'You need to supply a Lot/Serial Number for product:\n- %(product)s',
                    product=product.display_name,
                ))
            uom = product.uom_id
            if ld.get('uom_id'):
                uom = self.env['uom.uom'].search([('id', '=', int(ld['uom_id']))], limit=1) or uom
            price_unit = float(ld.get('price_unit') or 0.0)
            qty_base = uom._compute_quantity(qty, product.uom_id)
            if float_compare(qty_base, 0.0, precision_rounding=product.uom_id.rounding) <= 0:
                raise UserError(_(
                    'Dispatch quantity for %s converts to zero in base unit (%s). '
                    'Check the UoM conversion factors.',
                    product.display_name, product.uom_id.display_name,
                ))
            line_commands.append(Command.create({
                'product_id': product.id,
                'lot_id': lot.id if lot else False,
                'product_uom_id': uom.id,
                'qty_dispatched': qty,
                'price_unit': price_unit,
            }))

        consignment = self.create({
            'dispatch_session_id': session.id,
            'partner_id': partner.id,
            'note': vals.get('note') or False,
            'line_ids': line_commands,
        })
        consignment._confirm_dispatch()
        return {
            'consignment_id': consignment.id,
            'consignment_name': consignment.name,
            'picking_name': consignment.dispatch_picking_id.name or '',
        }

    @api.model
    def action_settle(self, consignment_id, settlement_data):
        """Process settlement of a dispatched consignment from the POS UI.

        settlement_data = {
            'session_id': int,
            'lines': [
                {
                    'line_id': int,            # pos.consignment.line id
                    'qty_sold': float,
                    'qty_returned_good': float,
                    'qty_returned_scrap': float,  # damaged/expired – goes to scrap
                }
            ],
        }
        Returns: {
            'consignment_id': int,
            'consignment_name': str,
            'sold_lines': [                   # lines to create POS order from in JS
                {
                    'product_id': int,
                    'product_name': str,
                    'qty': float,
                    'price_unit': float,
                    'tax_ids': [...],
                    'uom_id': int,
                }
            ],
            'partner_id': int,
            'amount_to_collect': float,
        }
        """
        consignment = self.search([('id', '=', int(consignment_id))], limit=1)
        if not consignment:
            raise UserError(_('Consignment record not found.'))
        if consignment.state != 'dispatched':
            raise UserError(_(
                'Consignment %s is not in Dispatched state (current: %s).',
                consignment.name, consignment.state,
            ))

        session = self.env['pos.session'].search([
            ('id', '=', int(settlement_data.get('session_id') or 0)),
            ('state', '=', 'opened'),
        ], limit=1)
        if not session:
            raise UserError(_('You need an open POS session to process a settlement.'))

        lines_by_id = {l.id: l for l in consignment.line_ids}
        line_updates = {}  # line_id -> {qty_sold, qty_returned_good, qty_returned_scrap}

        for ld in (settlement_data.get('lines') or []):
            line_id = int(ld.get('line_id') or 0)
            line = lines_by_id.get(line_id)
            if not line:
                raise UserError(_('Settlement line id %s not found in consignment.', line_id))
            qty_sold = float(ld.get('qty_sold') or 0.0)
            qty_good = float(ld.get('qty_returned_good') or 0.0)
            qty_scrap = float(ld.get('qty_returned_scrap') or 0.0)
            base_uom = line.base_uom_id or line.product_id.uom_id
            rounding = base_uom.rounding
            total_accounted = float_round(qty_sold + qty_good + qty_scrap, precision_rounding=rounding)
            if float_compare(total_accounted, line.qty_dispatched_base, precision_rounding=rounding) != 0:
                raise UserError(_(
                    'Line %s: qty_sold (%(sold)s) + qty_returned_good (%(good)s) + '
                    'qty_returned_scrap (%(scrap)s) = %(total)s %(uom)s but dispatched qty is '
                    '%(dispatched)s %(uom)s. All dispatched quantities must be accounted for.',
                    line.product_id.display_name,
                    sold=qty_sold,
                    good=qty_good,
                    scrap=qty_scrap,
                    total=total_accounted,
                    dispatched=line.qty_dispatched_base,
                    uom=base_uom.display_name,
                ))
            line_updates[line_id] = {
                'qty_sold': qty_sold,
                'qty_returned_good': qty_good,
                'qty_returned_scrap': qty_scrap,
            }

        with self.env.cr.savepoint():
            consignment._process_settlement(session, line_updates)

        sold_lines = []
        resale_lines = []
        amount = 0.0
        amount_resale = 0.0
        for line in consignment.line_ids:
            upd = line_updates.get(line.id, {})
            qty_sold = upd.get('qty_sold', 0.0)
            qty_good = upd.get('qty_returned_good', 0.0)
            base_uom = line.base_uom_id or line.product_id.uom_id
            if not float_is_zero(qty_sold, precision_rounding=base_uom.rounding):
                taxes = line.product_id.taxes_id.filtered(
                    lambda t: t.company_id == consignment.company_id
                )
                sold_lines.append({
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.display_name,
                    'qty': qty_sold,
                    'price_unit': line.price_unit_base,
                    'tax_ids': taxes.ids,
                    'uom_id': base_uom.id,
                    'uom_name': base_uom.display_name,
                })
                amount += qty_sold * line.price_unit_base
            if not float_is_zero(qty_good, precision_rounding=base_uom.rounding) and line.return_lot_id:
                taxes = line.product_id.taxes_id.filtered(
                    lambda t: t.company_id == consignment.company_id
                )
                resale_lines.append({
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.display_name,
                    'qty': qty_good,
                    'price_unit': line.price_unit_base,
                    'tax_ids': taxes.ids,
                    'uom_id': base_uom.id,
                    'uom_name': base_uom.display_name,
                    'lot_id': line.return_lot_id.id,
                    'lot_name': line.return_lot_id.name,
                    'consignment_line_id': line.id,
                })
                amount_resale += qty_good * line.price_unit_base

        return {
            'consignment_id': consignment.id,
            'consignment_name': consignment.name,
            'sold_lines': sold_lines,
            'resale_lines': resale_lines,
            'partner_id': consignment.partner_id.id,
            'partner_name': consignment.partner_id.display_name,
            'amount_to_collect': amount,
            'amount_resale': amount_resale,
        }

    # -------------------------------------------------------------------------
    # Internal dispatch & settlement logic
    # -------------------------------------------------------------------------

    def _confirm_dispatch(self):
        """Create the outbound dispatch picking and transition to Dispatched."""
        self.ensure_one()
        self._check_consignment_config()
        if not self.line_ids:
            raise UserError(_('Add at least one product line before dispatching.'))
        with self.env.cr.savepoint():
            picking = self._create_dispatch_picking()
            self.write({
                'state': 'dispatched',
                'dispatch_date': fields.Datetime.now(),
                'dispatch_picking_id': picking.id,
            })
        return True

    def _check_consignment_config(self):
        self.ensure_one()
        config = self.dispatch_session_id.config_id
        if not config:
            config = self.env['pos.config'].search([('id', '=', self.config_id.id)], limit=1)
        missing = []
        if not config.consignment_location_id:
            missing.append(_('Consignment Transit Location'))
        if not config.consignment_return_location_id:
            missing.append(_('Consignment Returns Staging'))
        if not config.picking_type_id:
            missing.append(_('Stock Operation Type'))
        if missing:
            raise UserError(_(
                'Configure the following on POS %s: %s',
                config.display_name,
                ', '.join(missing),
            ))

    def _consignment_location(self):
        """Return the configured consignment transit location."""
        self.ensure_one()
        config = self.dispatch_session_id.config_id or self.settlement_session_id.config_id
        loc = config.consignment_location_id
        if not loc:
            raise UserError(_(
                'No Consignment Transit Location configured for POS %s.',
                config.display_name,
            ))
        return loc

    def _consignment_return_location(self):
        """Return staging location for loose good returns awaiting resale."""
        self.ensure_one()
        config = self.dispatch_session_id.config_id or self.settlement_session_id.config_id
        loc = config.consignment_return_location_id
        if not loc:
            raise UserError(_(
                'No Consignment Returns Staging location configured for POS %s.',
                config.display_name,
            ))
        return loc

    def _inventory_adjustment_location(self):
        """Virtual inventory location used for lot relabelling during good returns."""
        self.ensure_one()
        loc = self.env['stock.location'].search([
            ('usage', '=', 'inventory'),
            ('company_id', 'in', [False, self.company_id.id]),
        ], limit=1)
        if not loc:
            raise UserError(_('No inventory adjustment location found for company %s.', self.company_id.name))
        return loc

    def _create_return_lot(self, line):
        """Create a new lot/serial for loose good-return pieces (not the dispatch lot)."""
        self.ensure_one()
        product = line.product_id
        seq = self.env['ir.sequence'].next_by_code('pos.consignment.return.lot') or line.id
        lot_name = '%s-R-%s' % (self.name.replace('/', '-'), seq)
        existing = self.env['stock.lot'].search([
            ('name', '=', lot_name),
            ('product_id', '=', product.id),
            ('company_id', 'in', [False, self.company_id.id]),
        ], limit=1)
        if existing:
            return existing
        return self.env['stock.lot'].create({
            'name': lot_name,
            'product_id': product.id,
            'company_id': self.company_id.id,
        })

    def _transfer_with_lot_change(self, picking, product, qty, uom, src, dest,
                                  src_lot, dest_lot, require_src_stock=True):
        """Move qty from src/src_lot to dest/dest_lot via inventory adjustment.

        Odoo move lines cannot change lot identity in a single step for tracked
        products. We consume under the dispatch lot, then receive under a new
        return lot — both steps recorded on the same internal picking.
        """
        if float_is_zero(qty, precision_rounding=uom.rounding):
            return
        inv_loc = self._inventory_adjustment_location()
        # Step 1: transit (dispatch lot) → inventory adjustment (consume dispatch lot)
        self._create_stock_move(
            picking=picking,
            product=product,
            qty=qty,
            uom=uom,
            lot=src_lot,
            src=src,
            dest=inv_loc,
            require_stock=require_src_stock,
        )
        # Step 2: inventory adjustment → staging (receive under new return lot)
        self._create_stock_move(
            picking=picking,
            product=product,
            qty=qty,
            uom=uom,
            lot=dest_lot,
            src=inv_loc,
            dest=dest,
            require_stock=False,
        )

    def _customer_location(self):
        """Return the customer virtual location for the partner."""
        self.ensure_one()
        partner = self.partner_id
        if partner and partner.property_stock_customer:
            return partner.property_stock_customer
        return self.env['stock.warehouse']._get_partner_locations()[0]

    def _warehouse_stock_location(self):
        """Return the main sellable stock location of the warehouse."""
        self.ensure_one()
        config = self.dispatch_session_id.config_id or self.settlement_session_id.config_id
        return config.picking_type_id.default_location_src_id or config.warehouse_id.lot_stock_id

    def _create_dispatch_picking(self):
        """Warehouse stock → Consignment Transit (immediate)."""
        self.ensure_one()
        config = self.dispatch_session_id.config_id
        picking_type = config.picking_type_id
        src_location = self._warehouse_stock_location()
        dest_location = self._consignment_location()

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': src_location.id,
            'location_dest_id': dest_location.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
            'pos_session_id': self.dispatch_session_id.id,
            'move_type': 'direct',
        })
        moves = self.env['stock.move']
        for line in self.line_ids:
            base_uom = line.base_uom_id or line.product_id.uom_id
            move = self._create_stock_move(
                picking=picking,
                product=line.product_id,
                qty=line.qty_dispatched_base,
                uom=base_uom,
                lot=line.lot_id,
                src=src_location,
                dest=dest_location,
                require_stock=True,
                auto_confirm=False,
            )
            if move:
                moves |= move
        if moves:
            moves._action_confirm(merge=False)
            moves._action_assign()
            moves.picked = True
        picking.with_context(skip_sms=True, cancel_backorder=True)._action_done()
        if picking.state != 'done':
            raise UserError(_(
                'Could not complete dispatch transfer for %s.', self.name
            ))
        return picking

    def _process_settlement(self, session, line_updates):
        """Execute all settlement stock moves and update consignment state.

        Called inside a savepoint from action_settle so all moves roll back together.
        """
        self.ensure_one()
        consignment_loc = self._consignment_location()
        return_staging_loc = self._consignment_return_location()
        customer_loc = self._customer_location()
        config = session.config_id

        int_picking_type = config.warehouse_id.int_type_id or self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', config.warehouse_id.id),
        ], limit=1)
        out_picking_type = config.picking_type_id

        return_picking = self.env['stock.picking']
        sold_picking = self.env['stock.picking']

        # --- Good returns: Transit (dispatch lot) → Returns Staging (NEW lot) ---
        good_lines = [
            (l, line_updates[l.id]) for l in self.line_ids
            if not float_is_zero(
                line_updates.get(l.id, {}).get('qty_returned_good', 0.0),
                precision_rounding=(l.base_uom_id or l.product_id.uom_id).rounding,
            )
        ]
        if good_lines:
            return_picking = self.env['stock.picking'].create({
                'picking_type_id': int_picking_type.id,
                'location_id': consignment_loc.id,
                'location_dest_id': return_staging_loc.id,
                'partner_id': self.partner_id.id,
                'origin': _('%s RETURN', self.name),
                'company_id': self.company_id.id,
                'pos_session_id': session.id,
                'move_type': 'direct',
            })
            for line, upd in good_lines:
                base_uom = line.base_uom_id or line.product_id.uom_id
                return_lot = self._create_return_lot(line)
                line.return_lot_id = return_lot
                self._transfer_with_lot_change(
                    picking=return_picking,
                    product=line.product_id,
                    qty=upd['qty_returned_good'],
                    uom=base_uom,
                    src=consignment_loc,
                    dest=return_staging_loc,
                    src_lot=line.lot_id,
                    dest_lot=return_lot,
                    require_src_stock=True,
                )
            return_picking.with_context(skip_sms=True, cancel_backorder=True)._action_done()
            if return_picking.state != 'done':
                raise UserError(_('Could not complete good-return transfer for %s.', self.name))

        # --- Scrap: damaged/expired from Consignment ---
        scrap_loc = config.exchange_scrap_location_id
        if not scrap_loc:
            scrap_loc = self.env['stock.location'].search([
                ('scrap_location', '=', True),
                ('company_id', 'in', [False, self.company_id.id]),
            ], limit=1)
        scraps = self.env['stock.scrap']
        for line in self.line_ids:
            upd = line_updates.get(line.id, {})
            base_uom = line.base_uom_id or line.product_id.uom_id
            qty_scrap = upd.get('qty_returned_scrap', 0.0)
            if float_is_zero(qty_scrap, precision_rounding=base_uom.rounding):
                continue
            if not scrap_loc:
                raise UserError(_('No scrap location configured. Set Exchange Scrap Location on POS config.'))
            scrap = self.env['stock.scrap'].create({
                'product_id': line.product_id.id,
                'product_uom_id': base_uom.id,
                'scrap_qty': qty_scrap,
                'lot_id': line.lot_id.id if line.lot_id else False,
                'location_id': consignment_loc.id,
                'scrap_location_id': scrap_loc.id,
                'origin': _('%s SCRAP', self.name),
                'company_id': self.company_id.id,
            })
            scrap.do_scrap()
            scraps |= scrap

        # --- Sold: Consignment → Customer ---
        sold_lines = [
            (l, line_updates[l.id]) for l in self.line_ids
            if not float_is_zero(
                line_updates.get(l.id, {}).get('qty_sold', 0.0),
                precision_rounding=(l.base_uom_id or l.product_id.uom_id).rounding,
            )
        ]
        if sold_lines:
            sold_picking = self.env['stock.picking'].create({
                'picking_type_id': out_picking_type.id,
                'location_id': consignment_loc.id,
                'location_dest_id': customer_loc.id,
                'partner_id': self.partner_id.id,
                'origin': _('%s SOLD', self.name),
                'company_id': self.company_id.id,
                'pos_session_id': session.id,
                'move_type': 'direct',
            })
            sold_moves = self.env['stock.move']
            for line, upd in sold_lines:
                base_uom = line.base_uom_id or line.product_id.uom_id
                move = self._create_stock_move(
                    picking=sold_picking,
                    product=line.product_id,
                    qty=upd['qty_sold'],
                    uom=base_uom,
                    lot=line.lot_id,
                    src=consignment_loc,
                    dest=customer_loc,
                    require_stock=True,
                    auto_confirm=False,
                )
                if move:
                    sold_moves |= move
            if sold_moves:
                sold_moves._action_confirm(merge=False)
                sold_moves._action_assign()
                sold_moves.picked = True
            sold_picking.with_context(skip_sms=True, cancel_backorder=True)._action_done()
            if sold_picking.state != 'done':
                raise UserError(_('Could not complete sold-transfer for %s.', self.name))

        # --- Update consignment line settlement qtys ---
        for line in self.line_ids:
            upd = line_updates.get(line.id, {})
            line.write({
                'qty_sold': upd.get('qty_sold', 0.0),
                'qty_returned_good': upd.get('qty_returned_good', 0.0),
                'qty_returned_scrap': upd.get('qty_returned_scrap', 0.0),
            })

        # Transition to settled; settlement POS order will be linked later by _process_saved_order
        write_vals = {
            'state': 'settled',
            'settlement_date': fields.Datetime.now(),
            'settlement_session_id': session.id,
        }
        if return_picking:
            write_vals['return_picking_ids'] = [Command.set(return_picking.ids)]
        if sold_picking:
            write_vals['sold_picking_id'] = sold_picking.id
        self.write(write_vals)
        return True

    def _create_stock_move(self, picking, product, qty, uom, lot, src, dest,
                           require_stock=False, auto_confirm=True):
        """Create a single stock.move inside `picking` with lot-specific move lines.

        When several lines share the same product on one picking (different lots),
        callers must pass ``auto_confirm=False`` and confirm all moves together with
        ``merge=False`` so Odoo does not merge and delete earlier moves.
        """
        if float_is_zero(qty, precision_rounding=uom.rounding):
            return self.env['stock.move']

        if require_stock and product.is_storable:
            available = self.env['stock.quant']._get_available_quantity(
                product, src,
                lot_id=lot if lot else None,
                strict=bool(lot),
            )
            if float_compare(available, qty, precision_rounding=uom.rounding) < 0:
                raise UserError(_(
                    'Not enough %(product)s%(lot)s in %(loc)s: '
                    'available %(available)s, need %(need)s.',
                    product=product.display_name,
                    lot=(' [%s]' % lot.name) if lot else '',
                    loc=src.display_name,
                    available=available,
                    need=qty,
                ))

        move = self.env['stock.move'].create({
            'origin': picking.origin,
            'product_id': product.id,
            'product_uom': uom.id,
            'product_uom_qty': qty,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'picking_id': picking.id,
            'picking_type_id': picking.picking_type_id.id,
            'company_id': self.company_id.id,
        })

        ml_vals_list = []
        if lot and require_stock and product.is_storable:
            quants = self.env['stock.quant'].search([
                ('product_id', '=', product.id),
                ('lot_id', '=', lot.id),
                ('quantity', '>', 0.0),
                ('location_id', 'child_of', src.id),
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
        else:
            ml_vals = {
                'move_id': move.id,
                'product_id': product.id,
                'product_uom_id': uom.id,
                'quantity': qty,
                'location_id': src.id,
                'location_dest_id': dest.id,
                'picking_id': picking.id,
                'company_id': self.company_id.id,
            }
            if lot:
                ml_vals['lot_id'] = lot.id
            ml_vals_list.append(ml_vals)

        self.env['stock.move.line'].create(ml_vals_list)

        if auto_confirm:
            move._action_confirm(merge=False)
            move._action_assign()
            move.picked = True
        return move

    # -------------------------------------------------------------------------
    # POS data loading
    # -------------------------------------------------------------------------

    @api.model
    def _load_pos_data_domain(self, data, config):
        return [('state', '=', 'dispatched'), ('config_id', '=', config.id)]

    @api.model
    def _load_pos_data_fields(self, config):
        return [
            'id', 'name', 'state', 'partner_id', 'dispatch_date',
            'amount_dispatched', 'amount_settled', 'line_ids', 'currency_id',
        ]

    @api.model
    def _unrelevant_records(self, config):
        return self.search([
            ('id', 'in', self.ids),
            '|',
            ('state', '!=', 'dispatched'),
            ('config_id', '!=', config.id),
        ]).ids


class PosConsignmentLine(models.Model):
    _name = 'pos.consignment.line'
    _description = 'POS Consignment Line'
    _inherit = ['pos.load.mixin']
    _check_company_auto = True

    consignment_id = fields.Many2one(
        'pos.consignment',
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
    lot_id = fields.Many2one(
        'stock.lot',
        string='Dispatch Lot / Serial',
        domain="[('product_id', '=', product_id)]",
        check_company=True,
        ondelete='restrict',
        help='Lot/serial of the sealed dispatch unit (e.g. full Jhola).',
    )
    return_lot_id = fields.Many2one(
        'stock.lot',
        string='Return Lot / Serial',
        domain="[('product_id', '=', product_id)]",
        check_company=True,
        ondelete='restrict',
        copy=False,
        help='New lot assigned to loose good-return pieces at settlement.',
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Dispatch UoM',
        required=True,
        ondelete='restrict',
        help='Unit of measure used when dispatching from POS (e.g. Jhola).',
    )
    base_uom_id = fields.Many2one(
        'uom.uom',
        string='Base UoM',
        related='product_id.uom_id',
        store=True,
        readonly=True,
    )
    qty_dispatched = fields.Float(
        string='Dispatched Qty',
        digits='Product Unit',
        required=True,
        default=1.0,
        help='Quantity in the dispatch UoM selected on the POS order line.',
    )
    qty_dispatched_base = fields.Float(
        string='Dispatched Qty (Base)',
        digits='Product Unit',
        compute='_compute_base_values',
        store=True,
        precompute=True,
        help='Quantity converted to the product base UoM for stock and settlement.',
    )
    price_unit = fields.Float(
        string='Unit Price',
        digits='Product Price',
        required=True,
        default=0.0,
        help='Price per dispatch UoM.',
    )
    price_unit_base = fields.Float(
        string='Unit Price (Base)',
        digits='Product Price',
        compute='_compute_base_values',
        store=True,
        precompute=True,
        help='Price per base UoM, used for settlement POS orders.',
    )
    qty_sold = fields.Float(
        string='Sold Qty',
        digits='Product Unit',
        default=0.0,
        help='Settled sold quantity in base UoM.',
    )
    qty_returned_good = fields.Float(
        string='Returned Good Qty',
        digits='Product Unit',
        default=0.0,
        help='Returned good quantity in base UoM.',
    )
    qty_returned_scrap = fields.Float(
        string='Returned Scrap Qty',
        digits='Product Unit',
        default=0.0,
        help='Scrapped quantity in base UoM.',
    )
    qty_unaccounted = fields.Float(
        string='Unaccounted Qty',
        digits='Product Unit',
        compute='_compute_qty_unaccounted',
        store=True,
    )
    company_id = fields.Many2one(
        related='consignment_id.company_id',
        store=True,
    )

    _dispatched_positive = models.Constraint(
        'CHECK(qty_dispatched > 0)',
        'Dispatched quantity must be positive.',
    )
    _settlement_le_dispatched = models.Constraint(
        'CHECK(qty_sold + qty_returned_good + qty_returned_scrap <= qty_dispatched_base + 0.000001)',
        'Sum of settled quantities cannot exceed dispatched base quantity.',
    )

    def _pos_line_payload(self):
        """Serialize line for POS settlement UI (dual UoM display)."""
        self.ensure_one()
        base = self.base_uom_id or self.product_id.uom_id
        return {
            'id': self.id,
            'product_id': self.product_id.id,
            'product_name': self.product_id.display_name,
            'uom_id': self.product_uom_id.id,
            'uom_name': self.product_uom_id.display_name,
            'qty_dispatched': self.qty_dispatched,
            'base_uom_id': base.id,
            'base_uom_name': base.display_name,
            'qty_dispatched_base': self.qty_dispatched_base,
            'price_unit': self.price_unit,
            'price_unit_base': self.price_unit_base,
            'lot_id': self.lot_id.id if self.lot_id else False,
            'lot_name': self.lot_id.name if self.lot_id else '',
        }

    @api.depends('qty_dispatched', 'product_uom_id', 'product_id', 'price_unit')
    def _compute_base_values(self):
        for line in self:
            if not line.product_id:
                line.qty_dispatched_base = line.qty_dispatched
                line.price_unit_base = line.price_unit
                continue
            base = line.product_id.uom_id
            dispatch_uom = line.product_uom_id or base
            line.qty_dispatched_base = dispatch_uom._compute_quantity(
                line.qty_dispatched, base,
            )
            line.price_unit_base = dispatch_uom._compute_price(line.price_unit, base)

    @api.depends('qty_dispatched_base', 'qty_sold', 'qty_returned_good', 'qty_returned_scrap', 'base_uom_id')
    def _compute_qty_unaccounted(self):
        for line in self:
            rounding = line.base_uom_id.rounding if line.base_uom_id else 0.01
            line.qty_unaccounted = float_round(
                line.qty_dispatched_base - line.qty_sold - line.qty_returned_good - line.qty_returned_scrap,
                precision_rounding=rounding,
            )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id

    @api.model
    def _load_pos_data_domain(self, data, config):
        consignment_ids = [c['id'] for c in data.get('pos.consignment', [])]
        if not consignment_ids:
            return [('id', '=', False)]
        return [('consignment_id', 'in', consignment_ids)]

    @api.model
    def _load_pos_data_fields(self, config):
        return [
            'id', 'consignment_id', 'product_id', 'lot_id', 'product_uom_id',
            'base_uom_id', 'qty_dispatched', 'qty_dispatched_base',
            'price_unit', 'price_unit_base',
        ]
