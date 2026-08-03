/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

/**
 * Single patch on PosOrder.prototype (which does NOT own these methods —
 * it inherits them from PosOrderAccounting).  Because patch() inserts a
 * shim *below* the target prototype in the chain, patching a prototype that
 * already owns the method would be shadowed.  Patching PosOrder.prototype
 * places our overrides *above* PosOrderAccounting.prototype so they are
 * found first by JS property lookup.
 */
patch(PosOrder.prototype, {
    /**
     * Carry dispatch-mode flag in uiState so it survives reactive updates.
     */
    initState() {
        super.initState();
        this.uiState.is_consignment_dispatch = false;
    },

    /**
     * Guard the actual crash site: during IndexedDB restore PosOrder.setup()
     * triggers _computeAllPrices before the one2many ``lines`` relation is
     * connected, leaving ``lines`` undefined or an unresolvable raw Set.
     * Return safe empty price data in that situation so setup() can finish;
     * _pricesDirty stays true and a real recompute happens on the next
     * ``order.prices`` access once lines are properly connected.
     */
    _computeAllPrices(opts = {}) {
        const lines = opts.lines || this.lines;
        if (!lines || !lines.map) {
            return {
                taxDetails: {
                    total_amount_currency: 0,
                    cash_rounding_base_amount_currency: 0,
                    order_sign: this.isRefund ? -1 : 1,
                    total_amount_no_rounding: 0,
                },
                baseLines: [],
                baseLineByLineUuids: {},
            };
        }
        return super._computeAllPrices(...arguments);
    },
});
