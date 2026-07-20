# -*- coding: utf-8 -*-
from odoo import fields, models, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_exchange = fields.Boolean(
        string='Is Exchange',
        default=False,
        copy=False,
        help='Zero-amount POS order created by a product exchange (no cash movement).',
    )
    exchange_id = fields.Many2one(
        'pos.exchange',
        string='Exchange',
        copy=False,
        index=True,
        ondelete='set null',
    )

    def _compute_order_name(self, session=None):
        if self.is_exchange:
            session = session or self.session_id
            last_reference_part = self.get_reference_last_part()
            prefix = session.config_id.order_seq_id.prefix or session.config_id.name
            suffix = f" - {session.config_id.order_seq_id.suffix}" if session.config_id.order_seq_id.suffix else ''
            return _('%(prefix)s - %(ref)s EXCHANGE%(suffix)s', prefix=prefix, ref=last_reference_part, suffix=suffix)
        return super()._compute_order_name(session=session)
