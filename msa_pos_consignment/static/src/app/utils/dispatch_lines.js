/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";

/**
 * Build pos.consignment.action_dispatch line payloads from POS order lines.
 * Reads lot/serial from pack_lot_ids (lot_name), same as native POS sync.
 */
export function buildDispatchLinesFromOrder(order) {
    const lines = [];
    for (const orderLine of order.lines) {
        const product = orderLine.product_id;
        const validLots = orderLine.getValidLots
            ? orderLine.getValidLots()
            : (orderLine.pack_lot_ids || []).filter((l) => l.lot_name);

        if (product.tracking === "serial") {
            if (!validLots.length) {
                lines.push(_baseLine(orderLine, product, orderLine.qty, false));
                continue;
            }
            for (const packLot of validLots) {
                lines.push(_baseLine(orderLine, product, 1, packLot.lot_name));
            }
        } else if (product.tracking === "lot") {
            const lotName = validLots[0]?.lot_name || false;
            lines.push(_baseLine(orderLine, product, orderLine.qty, lotName));
        } else {
            lines.push(_baseLine(orderLine, product, orderLine.qty, false));
        }
    }
    return lines;
}

/** UoM from msa_pos_uom line selector; serial lines always use product base UoM. */
function _lineUom(orderLine, product) {
    if (product.tracking === "serial") {
        return product.uom_id;
    }
    return orderLine.getUnit?.() || orderLine.product_uom_id || product.uom_id;
}

function _baseLine(orderLine, product, qty, lotName) {
    const uom = _lineUom(orderLine, product);
    return {
        product_id: product.id,
        qty,
        price_unit: orderLine.price_unit,
        uom_id: uom?.id || false,
        lot_name: lotName || false,
    };
}

/** Return first validation error message, or null if all lines are OK. */
export function validateDispatchOrderLines(order) {
    for (const line of order.lines) {
        const product = line.product_id;
        if (product.tracking === "none") {
            continue;
        }
        if (!line.hasValidProductLot?.()) {
            const label =
                product.tracking === "serial"
                    ? _t("serial number")
                    : _t("lot number");
            return _t(
                "%(product)s requires a %(label)s. Set it on the order line before dispatching.",
                { product: product.display_name, label }
            );
        }
    }
    return null;
}
