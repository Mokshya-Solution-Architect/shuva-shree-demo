from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_product_catalog_order_data(self, products, **kwargs):
        res = super()._get_product_catalog_order_data(products, **kwargs)
        for product in products:
            tmpl = product.product_tmpl_id
            uom = tmpl._get_default_sales_uom()
            if uom:
                res[product.id]["uomDisplayName"] = uom.display_name
        return res

    def _update_order_line_info(
        self, product_id, quantity, *, section_id=False, child_field="order_line", **kwargs
    ):
        self.ensure_one()
        price = super()._update_order_line_info(
            product_id,
            quantity,
            section_id=section_id,
            child_field=child_field,
            **kwargs,
        )

        if quantity <= 0:
            return price

        target_section_id = section_id or False
        lines = self.order_line.filtered(
            lambda l: (
                not l.display_type
                and l.product_id.id == product_id
                and (l.get_parent_section_line().id or False) == target_section_id
            )
        )

        for line in lines:
            tmpl = line.product_id.product_tmpl_id
            uom = tmpl._get_default_sales_uom()
            if uom and line.product_uom_id != uom:
                line.product_uom_id = uom.id
                line._reset_price_unit()
                price = line._get_discounted_price()

        return price


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("product_id")
    def _onchange_product_id(self):
        super()._onchange_product_id()
        for line in self:
            if not line.product_id:
                continue
            tmpl = line.product_id.product_tmpl_id
            uom = tmpl._get_default_sales_uom()
            if uom:
                line.product_uom_id = uom.id
                line._reset_price_unit()
