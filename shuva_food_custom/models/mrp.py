from odoo import fields, models

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    shuva_alt_qty = fields.Float(string='Finished Alt Qty / Pack Count', digits='Product Unit of Measure')
    shuva_pack_type_id = fields.Many2one('shuva.pack.type', string='Finished Pack Type')
    shuva_finished_pack_qty = fields.Float(string='Qty per Finished Pack', digits='Product Unit of Measure')

    def action_open_shuva_finished_pack_wizard(self):
        self.ensure_one()
        return {
            'name': 'Generate Finished Pack Barcodes',
            'type': 'ir.actions.act_window',
            'res_model': 'shuva.mrp.finished.pack.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_production_id': self.id},
        }

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    shuva_note = fields.Char(string='Shuva Note')

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    shuva_expected_variance_note = fields.Char(string='Variance Note')
