# -*- coding: utf-8 -*-


def _post_init_link_vrw_move_lines(env):
    """Link orphaned VRW move lines back to their picking.

    Older wizard versions created stock.move.line with move_id only, so
    Detailed Operations (domain: picking_id) stayed empty after validate.
    """
    env.cr.execute(
        """
        UPDATE stock_move_line AS sml
           SET picking_id = sm.picking_id
          FROM stock_move AS sm
         WHERE sml.move_id = sm.id
           AND sml.picking_id IS NULL
           AND sm.picking_id IS NOT NULL
        """
    )
