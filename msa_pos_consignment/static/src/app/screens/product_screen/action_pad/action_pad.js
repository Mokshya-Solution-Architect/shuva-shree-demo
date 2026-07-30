/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { useAsyncLockedMethod } from "@point_of_sale/app/hooks/hooks";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { SettlementListPopup } from "@msa_pos_consignment/app/components/settlement_popup/settlement_list_popup";
import {
    logConsignment,
    errorConsignment,
    snapshotOrder,
    snapshotPosContext,
} from "@msa_pos_consignment/app/utils/consignment_debug";
import {
    buildDispatchLinesFromOrder,
    validateDispatchOrderLines,
} from "@msa_pos_consignment/app/utils/dispatch_lines";

patch(ActionpadWidget.prototype, {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.confirmDispatch = useAsyncLockedMethod(this.confirmDispatch);
    },

    get isDispatchMode() {
        const order = this.pos.getOrder();
        return order?.uiState?.is_consignment_dispatch === true;
    },

    /** Mark the current order as a consignment dispatch basket (no new order). */
    clickConsignmentDispatch() {
        const order = this.pos.getOrder();
        if (!order) {
            return;
        }
        logConsignment("ActionpadWidget.clickConsignmentDispatch", "toggle on current order", {
            order: snapshotOrder(order),
            context: snapshotPosContext(this.pos),
        });
        if (order.uiState.is_consignment_dispatch) {
            this.cancelDispatchMode();
            return;
        }
        order.uiState.is_consignment_dispatch = true;
        this.notification.add(
            _t("Dispatch mode — add products, set the distributor, then confirm."),
            { type: "info" }
        );
    },

    cancelDispatchMode() {
        const order = this.pos.getOrder();
        if (order?.uiState) {
            order.uiState.is_consignment_dispatch = false;
        }
    },

    async clickConsignmentSettle() {
        await makeAwaitable(this.dialog, SettlementListPopup);
    },

    async confirmDispatch() {
        const order = this.pos.getOrder();
        logConsignment("ActionpadWidget.confirmDispatch", "called", {
            order: snapshotOrder(order),
            context: snapshotPosContext(this.pos),
        });

        if (!order) {
            return;
        }

        if (!order.partner_id) {
            this.notification.add(
                _t("Select a distributor first (use the Customer button)."),
                { type: "warning" }
            );
            return;
        }

        if (order.isEmpty()) {
            this.notification.add(
                _t("Add at least one product before confirming the dispatch."),
                { type: "warning" }
            );
            return;
        }

        const lotError = validateDispatchOrderLines(order);
        if (lotError) {
            this.notification.add(lotError, { type: "warning" });
            return;
        }

        const rpcPayload = {
            session_id: this.pos.session.id,
            partner_id: order.partner_id.id,
            lines: buildDispatchLinesFromOrder(order),
            note: false,
        };

        try {
            const result = await this.pos.data.call(
                "pos.consignment",
                "action_dispatch",
                [rpcPayload]
            );

            this.notification.add(
                _t(
                    "Dispatch %(ref)s created — transfer %(picking)s completed.",
                    {
                        ref: result.consignment_name,
                        picking: result.picking_name,
                    }
                ),
                { type: "success" }
            );

            this._clearOrderAfterDispatch(order);
        } catch (error) {
            errorConsignment("ActionpadWidget.confirmDispatch", "RPC failed", {
                message: error?.data?.message || error?.message,
            });
            this.notification.add(
                error?.data?.message || error?.message || _t("Dispatch failed. Please try again."),
                { type: "danger" }
            );
        }
    },

    _clearOrderAfterDispatch(order) {
        [...order.lines].forEach((line) => {
            this.pos.models["pos.order.line"].delete(line);
        });
        order.uiState.is_consignment_dispatch = false;
        if (order.partner_id) {
            // Core setPartner() does not accept null (reads partner.is_company).
            order.assertEditable();
            order.partner_id = false;
            order.updatePricelistAndFiscalPosition(false);
        }
    },
});
