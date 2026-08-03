/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { _t } from "@web/core/l10n/translation";
import { logConsignment, snapshotOrder, snapshotPosContext } from "@msa_pos_consignment/app/utils/consignment_debug";
import {
    getLineLotName,
    isConsignmentReturnLine,
} from "@msa_pos_consignment/app/utils/dispatch_lines";

/**
 * After settlement payment, open a resale order pre-filled with good-return
 * lines (new lots in Consignment Returns staging). Cashier can add fresh
 * warehouse products before collecting payment.
 */
export async function createConsignmentResaleOrder(pos, result) {
    const resaleLines = result.resale_lines || [];
    if (!resaleLines.length) {
        return null;
    }

    const newOrder = pos.addNewOrder();
    if (result.partner_id) {
        const partner = pos.models["res.partner"].get(result.partner_id);
        if (partner) {
            newOrder.setPartner(partner);
        }
    }
    newOrder.is_consignment_resale = true;
    if (newOrder.uiState) {
        newOrder.uiState.is_consignment_dispatch = true;
    }
    if (result.consignment_id) {
        const consignment = pos.models["pos.consignment"]?.get(result.consignment_id);
        newOrder.consignment_id = consignment || result.consignment_id;
    }

    for (const resaleLine of resaleLines) {
        const product = pos.models["product.product"].get(resaleLine.product_id);
        if (!product) {
            continue;
        }
        const baseUom = product.uom_id;
        await pos.addLineToCurrentOrder(
            {
                product_id: product,
                product_tmpl_id: product.product_tmpl_id,
                product_uom_id: baseUom,
                qty: resaleLine.qty,
                price_unit: resaleLine.price_unit,
            },
            { merge: false },
            false
        );
        const line = newOrder.getLastOrderline?.() || newOrder.lines.at(-1);
        if (!line) {
            continue;
        }
        line.is_consignment_return = true;
        if (resaleLine.lot_id) {
            line.consignmentReturnLotDbId = resaleLine.lot_id;
        }
        if (resaleLine.lot_name && product.tracking !== "none") {
            line.consignment_return_lot_name = resaleLine.lot_name;
            line.setPackLotLines({
                modifiedPackLotLines: {},
                newPackLotLines: [{ lot_name: resaleLine.lot_name }],
                setQuantity: false,
            });
        }
    }

    pos.setOrder(newOrder);
    logConsignment("createConsignmentResaleOrder", "created", {
        order: snapshotOrder(newOrder),
        context: snapshotPosContext(pos),
    });
    return newOrder;
}

/**
 * Repair return-line flags / pack lots for one order (e.g. drafts from before
 * is_consignment_return was persisted). Called at dispatch time only — not on
 * every POS boot, to avoid slowing session open.
 */
export function healConsignmentReturnLinesForOrder(pos, order) {
    if (!order) {
        return;
    }
    for (const line of order.lines || []) {
        if (!isConsignmentReturnLine(line, order)) {
            continue;
        }
        line.is_consignment_return = true;
        const lotName = getLineLotName(line);
        if (lotName && !line.consignment_return_lot_name) {
            line.consignment_return_lot_name = lotName;
        }
        if (lotName && !(line.pack_lot_ids && line.pack_lot_ids.length)) {
            pos.models["pos.pack.operation.lot"].create({
                lot_name: lotName,
                pos_order_line_id: line,
            });
        }
    }
}

patch(PosStore.prototype, {
    async setup(env, deps) {
        const result = await super.setup(env, deps);
        this.pendingConsignmentResale = null;

        // Restore pack_lot_ids for consignment return lines on every boot.
        // pos.pack.operation.lot records are in-memory only — not stored in
        // IndexedDB — so they vanish on reload. consignment_return_lot_name IS
        // a real DB field on pos.order.line, so we rebuild lot entries from it.
        for (const order of this.models["pos.order"].getAll()) {
            healConsignmentReturnLinesForOrder(this, order);
        }

        return result;
    },
});

patch(OrderPaymentValidation.prototype, {
    async afterOrderValidation() {
        await super.afterOrderValidation(...arguments);
        const order = this.order;
        const pending = this.pos.pendingConsignmentResale;
        if (order?.is_consignment_settlement && pending?.resale_lines?.length) {
            this.pos.pendingConsignmentResale = null;
            await createConsignmentResaleOrder(this.pos, pending);
            this.pos.notification.add(
                _t(
                    "Good-return stock loaded — add fresh warehouse products if needed, then confirm dispatch."
                ),
                { type: "info" }
            );
            this.pos.navigate("ProductScreen");
        }
    },
});
