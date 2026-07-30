# -*- coding: utf-8 -*-


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['stock.warehouse']._ss_ensure_consignment_location()
    env['pos.config']._ss_configure_consignment_defaults()
