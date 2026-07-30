/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { logConsignment } from "@msa_pos_consignment/app/utils/consignment_debug";

/**
 * Extend PosOrder.initState to carry dispatch-mode flags in uiState.
 *
 * These are LOCAL-ONLY fields — they live in uiState which is never
 * serialised to the server. Lines are cleared locally after a successful
 * dispatch RPC; the order is never paid while in dispatch mode.
 *
 *   is_consignment_dispatch  — true while this order is being used as
 *                              a "dispatch basket"
 */
patch(PosOrder.prototype, {
    initState() {
        super.initState();
        this.uiState.is_consignment_dispatch = false;
        logConsignment("PosOrder.initState", "uiState initialized", {
            uuid: this.uuid,
        });
    },
});
