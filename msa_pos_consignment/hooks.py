# -*- coding: utf-8 -*-


def post_init_hook(env):
    env['stock.warehouse']._ss_ensure_consignment_location()
    env['pos.config']._ss_configure_consignment_defaults()
