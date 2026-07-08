/** @odoo-module **/

/*
 * Best-effort Odoo 19 POS extension.
 * Purpose: when the cashier scans a generated pack/lot barcode, ask backend
 * which product and quantity it represents, then add that product to the order.
 * If your final Odoo 19 POS barcode service method name differs, keep the
 * backend method `stock.lot.shuva_pos_lookup_pack_barcode` and adjust only this file.
 */

import { patch } from "@web/core/utils/patch";
import { BarcodeReader } from "@point_of_sale/app/barcode/barcode_reader";

patch(BarcodeReader.prototype, {
    async scan(code) {
        const barcode = typeof code === "string" ? code : (code && code.code);
        if (barcode && this.env?.services?.orm && this.env?.services?.pos) {
            const pack = await this.env.services.orm.call(
                "stock.lot",
                "shuva_pos_lookup_pack_barcode",
                [barcode]
            );
            if (pack && pack.product_id) {
                const pos = this.env.services.pos;
                const product = pos.models?.["product.product"]?.get?.(pack.product_id) || pos.db?.get_product_by_id?.(pack.product_id);
                if (product && pos.get_order) {
                    const order = pos.get_order();
                    order.add_product(product, { quantity: pack.qty, merge: false });
                    const line = order.get_selected_orderline && order.get_selected_orderline();
                    if (line) {
                        line.shuva_pack_barcode = pack.pack_barcode;
                        line.shuva_lot_name = pack.lot_name;
                    }
                    return true;
                }
            }
        }
        return super.scan(...arguments);
    },
});
