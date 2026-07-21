/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { ExchangePopup } from "@msa_pos_exchange/app/components/popups/exchange_popup/exchange_popup";

patch(ControlButtons.prototype, {
    async clickExchange() {
        await makeAwaitable(this.dialog, ExchangePopup);
    },
});
