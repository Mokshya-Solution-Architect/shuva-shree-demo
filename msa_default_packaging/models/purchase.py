from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _get_product_catalog_order_data(self, products, **kwargs):
        res = super()._get_product_catalog_order_data(products, **kwargs)
        for product in products:
            tmpl = product.product_tmpl_id
            uom = tmpl._get_default_purchase_uom()
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
            uom = tmpl._get_default_purchase_uom()
            if uom and line.product_uom_id != uom:
                line.product_uom_id = uom.id
                line._compute_price_unit_and_date_planned_and_name()
                price = line.price_unit_discounted

        return price


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.depends(
        'product_id',
        'product_id.uom_id',
        'product_id.uom_ids',
        'product_id.seller_ids',
        'product_id.seller_ids.product_uom_id',
        'product_id.product_tmpl_id.purchase_default_packaging_id',
    )
    def _compute_allowed_uom_ids(self):
        super()._compute_allowed_uom_ids()
        for line in self:
            default_uom = line.product_id.product_tmpl_id.purchase_default_packaging_id
            if default_uom:
                line.allowed_uom_ids |= default_uom

    def _product_id_change(self):
        super()._product_id_change()
        for line in self:
            if not line.product_id:
                continue
            uom = line.product_id.product_tmpl_id._get_default_purchase_uom()
            if not uom:
                continue
            line.product_uom_id = uom
            line._compute_price_unit_and_date_planned_and_name()
