/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";

/** Settlement return lots are named e.g. CSG-2026-00001-R-0001 */
const RETURN_LOT_NAME_PATTERN = /-R-\d+$/;

/**
 * Detect good-return lines, including orders created before is_consignment_return
 * was persisted (IndexedDB draft lines that only have the return lot name).
 */
export function getLineLotName(orderLine) {
    const validLots = orderLine.getValidLots
        ? orderLine.getValidLots()
        : (orderLine.pack_lot_ids || []).filter((l) => l.lot_name);
    return validLots[0]?.lot_name || orderLine.consignment_return_lot_name || "";
}

export function isConsignmentReturnLine(orderLine, order = null) {
    if (orderLine.is_consignment_return) {
        return true;
    }
    if (orderLine.consignment_return_lot_name || orderLine.consignmentReturnLotDbId) {
        return true;
    }
    const lotName = getLineLotName(orderLine);
    if (lotName && RETURN_LOT_NAME_PATTERN.test(lotName)) {
        return true;
    }
    if (order?.is_consignment_resale && lotName && lotName.includes("-R-")) {
        return true;
    }
    return false;
}

/**
 * Build pos.consignment.action_dispatch line payloads from POS order lines.
 * Reads lot/serial from pack_lot_ids (lot_name), same as native POS sync.
 */
export function buildDispatchLinesFromOrder(order) {
    const lines = [];
    for (const orderLine of order.lines || []) {
        const product = orderLine.product_id;
        const validLots = orderLine.getValidLots
            ? orderLine.getValidLots()
            : (orderLine.pack_lot_ids || []).filter((l) => l.lot_name);

        if (product.tracking === "serial") {
            if (!validLots.length) {
                lines.push(_baseLine(orderLine, product, orderLine.qty, false, order));
                continue;
            }
            for (const packLot of validLots) {
                lines.push(_baseLine(orderLine, product, 1, packLot.lot_name, order));
            }
        } else if (product.tracking === "lot") {
            const lotName = validLots[0]?.lot_name || false;
            lines.push(_baseLine(orderLine, product, orderLine.qty, lotName, order));
        } else {
            lines.push(_baseLine(orderLine, product, orderLine.qty, false, order));
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

function _baseLine(orderLine, product, qty, lotName, order) {
    const uom = _lineUom(orderLine, product);
    const isReturn = isConsignmentReturnLine(orderLine, order);
    const lotId = isReturn ? orderLine.consignmentReturnLotDbId || false : false;
    return {
        product_id: product.id,
        qty,
        price_unit: orderLine.price_unit,
        uom_id: uom?.id || false,
        lot_name: lotName || false,
        lot_id: isReturn ? lotId || false : false,
        is_consignment_return: isReturn,
    };
}

/** Return first validation error message, or null if all lines are OK. */
export function validateDispatchOrderLines(order) {
    for (const line of order.lines || []) {
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
