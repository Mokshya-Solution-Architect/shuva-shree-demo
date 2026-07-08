from odoo import fields, models, tools

class ShuvaBarcodeHistoryReport(models.Model):
    _name = 'shuva.barcode.history.report'
    _description = 'Pack Barcode History'
    _auto = False
    _order = 'date desc'

    date = fields.Datetime(readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    lot_id = fields.Many2one('stock.lot', readonly=True)
    pack_barcode = fields.Char(readonly=True)
    picking_id = fields.Many2one('stock.picking', readonly=True)
    location_id = fields.Many2one('stock.location', readonly=True)
    location_dest_id = fields.Many2one('stock.location', readonly=True)
    qty_done = fields.Float(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    sml.id AS id,
                    COALESCE(sml.date, sm.date) AS date,
                    sml.product_id AS product_id,
                    sml.lot_id AS lot_id,
                    lot.shuva_pack_barcode AS pack_barcode,
                    sm.picking_id AS picking_id,
                    sml.location_id AS location_id,
                    sml.location_dest_id AS location_dest_id,
                    sml.quantity AS qty_done
                FROM stock_move_line sml
                JOIN stock_move sm ON sm.id = sml.move_id
                LEFT JOIN stock_lot lot ON lot.id = sml.lot_id
                WHERE sml.lot_id IS NOT NULL
            )
        """)

class ShuvaMrpVarianceReport(models.Model):
    _name = 'shuva.mrp.variance.report'
    _description = 'MRP Consumption Variance'
    _auto = False

    production_id = fields.Many2one('mrp.production', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    component_id = fields.Many2one('product.product', readonly=True)
    planned_qty = fields.Float(readonly=True)
    actual_qty = fields.Float(readonly=True)
    variance_qty = fields.Float(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    sm.id AS id,
                    sm.raw_material_production_id AS production_id,
                    mp.product_id AS product_id,
                    sm.product_id AS component_id,
                    sm.product_uom_qty AS planned_qty,
                    COALESCE(SUM(sml.quantity), 0.0) AS actual_qty,
                    COALESCE(SUM(sml.quantity), 0.0) - sm.product_uom_qty AS variance_qty
                FROM stock_move sm
                JOIN mrp_production mp ON mp.id = sm.raw_material_production_id
                LEFT JOIN stock_move_line sml ON sml.move_id = sm.id
                WHERE sm.raw_material_production_id IS NOT NULL
                GROUP BY sm.id, sm.raw_material_production_id, mp.product_id, sm.product_id, sm.product_uom_qty
            )
        """)
