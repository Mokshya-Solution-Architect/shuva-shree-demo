/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { PosStore } from "@point_of_sale/app/services/pos_store";


patch(PosOrderline.prototype, {


    getUnit() {
        return this.product_uom_id || this.product_id?.uom_id;
    },


    canBeMergedWith(other) {
        if (!super.canBeMergedWith(other)) {
            return false;
        }
        const thisUom = this.product_uom_id?.id || this.product_id?.uom_id?.id;
        const otherUom = other.product_uom_id?.id || other.product_id?.uom_id?.id;
        return thisUom === otherUom;
    },


    setUom(newUom) {
        const currentUom = this.product_uom_id || this.product_id?.uom_id;
        if (!currentUom || !newUom || currentUom.id === newUom.id) {
            return;
        }
        const scaledPrice = this.price_unit * (newUom.factor / currentUom.factor);
        this.product_uom_id = newUom;
        this.setUnitPrice(scaledPrice);
    },
});



patch(PosStore.prototype, {

    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        if (!vals.product_uom_id) {
            const tmpl = vals.product_tmpl_id;
            const defaultUom = tmpl && typeof tmpl === 'object'
                ? tmpl.sales_default_packaging_id
                : null;
            if (defaultUom) {
                vals = { ...vals, product_uom_id: defaultUom };
            }
        }
        return super.addLineToCurrentOrder(vals, opts, configure);
    },


    handlePriceUnit(values, order, price_unit) {
        super.handlePriceUnit(values, order, price_unit);

        const lineUom = values.product_uom_id;
        const baseUom = values.product_id?.uom_id;
        if (
            lineUom &&
            baseUom &&
            lineUom.id !== baseUom.id &&
            values.price_unit !== undefined &&
            values.price_unit !== 0
        ) {
            values.price_unit = values.price_unit * (lineUom.factor / baseUom.factor);
        }
    },
});
