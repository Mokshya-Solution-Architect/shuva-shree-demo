/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { ExchangePopup } from "@ss_pos_exchange/app/components/popups/exchange_popup/exchange_popup";

patch(TicketScreen.prototype, {
    async onClickExchange() {
        const order = this.getSelectedOrder();
        const lineId = this.getSelectedOrderlineId();
        let originLotName = "";
        let originOrderLineId = false;
        const partnerId = order?.getPartner?.()?.id || order?.partner_id?.id || false;

        if (lineId && order) {
            const line =
                (typeof order.getOrderline === "function" && order.getOrderline(lineId)) ||
                order.lines?.find((l) => l.id === lineId);
            if (line) {
                originOrderLineId = line.id;
                const packLots = line.pack_lot_ids || [];
                if (packLots.length) {
                    originLotName = packLots[0].lot_name || "";
                }
            }
        }

        await makeAwaitable(this.dialog, ExchangePopup, {
            originLotName,
            originOrderLineId,
            partnerId,
        });
    },
});
