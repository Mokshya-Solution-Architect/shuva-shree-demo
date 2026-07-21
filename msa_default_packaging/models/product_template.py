from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sales_default_packaging_id = fields.Many2one(
        "uom.uom",
        string="Sales Default Packaging",
        domain="[('id', 'in', uom_ids)]",
        help="Pick from Packagings only. If empty, the product Unit (e.g. EA) is used on sales lines.",
    )
    purchase_default_packaging_id = fields.Many2one(
        "uom.uom",
        string="Purchase Default Packaging",
        help="Any UoM. If empty, the product Unit (e.g. EA) is used on purchase lines.",
    )

    def _get_default_sales_uom(self):
        self.ensure_one()
        uom = self.sales_default_packaging_id
        return uom if uom and uom in self.uom_ids else False

    def _get_default_purchase_uom(self):
        self.ensure_one()
        return self.purchase_default_packaging_id or False

    @staticmethod
    def _removed_ids_from_m2m_commands(commands, existing_ids):
        """Net-removed m2m ids: initial set minus set after applying all commands in order."""
        before = set(existing_ids or [])
        current = set(before)
        for cmd in commands or []:
            if not cmd:
                continue
            op = cmd[0]
            if op in (2, 3):
                if len(cmd) > 1:
                    current.discard(cmd[1])
            elif op == 4:
                if len(cmd) > 1:
                    current.add(cmd[1])
            elif op == 5:
                current.clear()
            elif op == 6:
                if len(cmd) > 2:
                    current = set(cmd[2] or [])
        return before - current

    def write(self, vals):
        tracked = {}
        if "uom_ids" in vals:
            for rec in self:
                tracked[rec.id] = {
                    "existing_uom_ids": rec.uom_ids.ids,
                    "old_sales_id": rec.sales_default_packaging_id.id,
                }

        res = super().write(vals)

        if "uom_ids" in vals:
            for rec in self:
                data = tracked.get(rec.id, {})
                removed_ids = self._removed_ids_from_m2m_commands(
                    vals["uom_ids"], data.get("existing_uom_ids", [])
                )
                allowed_now = set(rec.uom_ids.ids)
                to_write = {}

                current_sales = rec.sales_default_packaging_id.id
                old_sales = data.get("old_sales_id")
                if "sales_default_packaging_id" in vals:
                    if current_sales and current_sales not in allowed_now:
                        to_write["sales_default_packaging_id"] = False
                else:
                    if old_sales in removed_ids:
                        to_write["sales_default_packaging_id"] = False
                    elif old_sales and old_sales in allowed_now and not current_sales:
                        to_write["sales_default_packaging_id"] = old_sales

                if to_write:
                    super(ProductTemplate, rec).write(to_write)

        return res
