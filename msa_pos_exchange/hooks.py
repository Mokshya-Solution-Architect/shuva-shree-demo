# -*- coding: utf-8 -*-


def post_init_hook(env):
    env['stock.warehouse']._ss_ensure_exchange_locations()
    env['pos.config']._ss_configure_exchange_defaults()
