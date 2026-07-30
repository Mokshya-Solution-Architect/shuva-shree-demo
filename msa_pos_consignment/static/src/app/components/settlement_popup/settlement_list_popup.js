/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { SettlementPopup } from "@msa_pos_consignment/app/components/settlement_popup/settlement_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";

/**
 * SettlementListPopup — shows all open (dispatched) consignments for a partner.
 * Cashier selects one → opens SettlementPopup for the actual settlement.
 */
export class SettlementListPopup extends Component {
    static template = "msa_pos_consignment.SettlementListPopup";
    static components = { Dialog };
    static props = {
        close: Function,
        getPayload: { type: Function, optional: true },
    };

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        const currentOrder = this.pos.getOrder();
        const partner = currentOrder?.getPartner?.() || null;

        this.state = useState({
            partnerId: partner?.id || false,
            partnerName: partner?.name || "",
            consignments: [],
            loading: false,
            error: "",
        });

        if (this.state.partnerId) {
            this._loadConsignments();
        }
    }

    get isSmallScreen() {
        return this.pos.isSmallProductScreen;
    }

    get dialogSize() {
        return this.isSmallScreen ? "fs" : "md";
    }

    get hasConsignments() {
        return this.state.consignments.length > 0;
    }

    async selectPartner() {
        const currentPartner = this.state.partnerId
            ? this.pos.models["res.partner"].get(this.state.partnerId)
            : false;
        const partner = await makeAwaitable(this.dialog, PartnerList, {
            partner: currentPartner || false,
        });
        if (partner) {
            this.state.partnerId = partner.id;
            this.state.partnerName = partner.name;
            await this._loadConsignments();
        }
    }

    async _loadConsignments() {
        if (!this.state.partnerId) {
            this.state.consignments = [];
            return;
        }
        this.state.loading = true;
        this.state.error = "";
        try {
            const result = await this.pos.data.call(
                "pos.consignment",
                "get_open_for_partner",
                [this.state.partnerId, this.pos.config.id]
            );
            this.state.consignments = result;
        } catch (error) {
            this.state.error =
                error?.data?.message || error?.message || _t("Failed to load consignments.");
            this.state.consignments = [];
        } finally {
            this.state.loading = false;
        }
    }

    formatDate(dateStr) {
        if (!dateStr) return "";
        try {
            return new Date(dateStr).toLocaleDateString();
        } catch {
            return dateStr;
        }
    }

    formatAmount(amount) {
        const currency = this.pos.currency;
        if (!currency) return String(amount);
        return currency.symbol + " " + Number(amount).toFixed(currency.decimal_places || 2);
    }

    async openSettlement(consignment) {
        const result = await makeAwaitable(this.dialog, SettlementPopup, {
            consignment,
            partnerId: this.state.partnerId,
            partnerName: this.state.partnerName,
        });
        if (result) {
            this.props.getPayload?.(result);
            this.props.close();
        }
    }

    cancel() {
        this.props.close();
    }
}
