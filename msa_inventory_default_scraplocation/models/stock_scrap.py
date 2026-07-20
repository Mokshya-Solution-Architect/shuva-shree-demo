from odoo import models, api

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    @api.model
    def default_get(self, fields_list):
        res = super(StockScrap, self).default_get(fields_list)
        
        if 'scrap_location_id' in fields_list:
            scrap_loc = self.env['stock.location'].search([
                ('name', '=', 'Scrap Location'),
            ], limit=1)
            
            if scrap_loc:
                res['scrap_location_id'] = scrap_loc.id
                
        return res