/** @odoo-module **/

import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useAsyncLockedMethod } from "@point_of_sale/app/hooks/hooks";
import { useBarcodeReader } from "@point_of_sale/app/hooks/barcode_reader_hook";

/**
 * Scan-first exchange wizard.
 * Flow: scan returned → tap reason → scan replacement → confirm (auto for serial).
 */
export class ExchangePopup extends Component {
    static template = "msa_pos_exchange.ExchangePopup";
    static components = { Dialog };
    static props = {
        close: Function,
        getPayload: { type: Function, optional: true },
        /** Prefill from Ticket Screen */
        originLotName: { type: String, optional: true },
        originOrderLineId: { type: [Number, Boolean], optional: true },
        partnerId: { type: [Number, Boolean], optional: true },
    };

    setup() {
        this.pos = usePos();
        this.notification = useService("notification");
        this.originInputRef = useRef("originLot");
        this.replacementInputRef = useRef("replacementLot");
        this.state = useState({
            step: "origin", // origin | reason | replacement | confirming
            originLotName: this.props.originLotName || "",
            replacementLotName: "",
            reason: "packaging_damage",
            returnedQty: "1",
            reusableQty: "1",
            note: "",
            busy: false,
            productName: "",
            tracking: "none",
            uomName: "",
            originOrderName: "",
            originOrderLineId: this.props.originOrderLineId || false,
            productId: false,
            availableFgQty: 0,
            error: "",
            statusHint: _t("Scan the returned lot / serial"),
        });
        this.confirm = useAsyncLockedMethod(this.confirm);

        // Exclusive barcode while dialog is open — raw SN often parses as "error"
        useBarcodeReader(
            {
                product: (code) => this._onBarcode(code),
                lot: (code) => this._onBarcode(code),
                weight: (code) => this._onBarcode(code),
                quantity: (code) => this._onBarcode(code),
                error: (code) => this._onBarcode(code),
            },
            true
        );

        onMounted(async () => {
            if (this.state.originLotName) {
                await this.resolveOriginLot();
            } else {
                this.originInputRef.el?.focus();
            }
        });
    }

    get scrapQty() {
        const returned = parseFloat(this.state.returnedQty) || 0;
        const reusable =
            this.state.reason === "expired" ? 0 : parseFloat(this.state.reusableQty) || 0;
        return Math.max(0, returned - reusable);
    }

    get showQtyFields() {
        return (
            this.state.productId &&
            this.state.tracking === "lot" &&
            this.state.reason === "packaging_damage"
        );
    }

    get canConfirm() {
        if (!this.state.productId || this.state.busy) {
            return false;
        }
        if (this.state.tracking !== "none" && !(this.state.replacementLotName || "").trim()) {
            return false;
        }
        return true;
    }

    _barcodeValue(code) {
        if (!code) {
            return "";
        }
        if (typeof code === "string") {
            return code.trim();
        }
        return (code.code || code.base_code || code.value || "").toString().trim();
    }

    async _onBarcode(code) {
        const value = this._barcodeValue(code);
        if (!value || this.state.busy) {
            return;
        }
        this.state.error = "";
        if (!this.state.productId || this.state.step === "origin") {
            this.state.originLotName = value;
            await this.resolveOriginLot();
            return;
        }
        this.state.replacementLotName = value;
        await this.resolveReplacementLot({ autoConfirm: this.state.tracking === "serial" });
    }

    onReasonSelect(reason) {
        this.state.reason = reason;
        if (reason === "expired") {
            this.state.reusableQty = "0";
        } else if (this.state.tracking === "serial") {
            this.state.reusableQty = "1";
            this.state.returnedQty = "1";
        } else if (this.state.tracking === "lot") {
            this.state.reusableQty = this.state.returnedQty;
        }
        this.state.step = "replacement";
        this.state.statusHint = _t("Scan the replacement lot / serial from Finished Goods");
        this.state.error = "";
        setTimeout(() => this.replacementInputRef.el?.focus(), 50);
    }

    async onOriginEnter(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            await this.resolveOriginLot();
        }
    }

    async onReplacementEnter(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            await this.resolveReplacementLot({
                autoConfirm: this.state.tracking === "serial",
            });
        }
    }

    async resolveOriginLot() {
        const lotName = (this.state.originLotName || "").trim();
        if (!lotName) {
            this.state.error = _t("Scan the returned lot / serial.");
            return;
        }
        this.state.busy = true;
        this.state.error = "";
        try {
            const data = await this.pos.data.call("pos.exchange", "lookup_lot_for_pos", [
                lotName,
                this.pos.config.id,
                "origin",
            ]);
            this.state.productName = data.product_name;
            this.state.tracking = data.tracking;
            this.state.uomName = data.uom_name;
            this.state.originOrderName = data.origin_order_name || "";
            this.state.originOrderLineId =
                this.state.originOrderLineId || data.origin_order_line_id || false;
            this.state.productId = data.product_id;
            this.state.returnedQty = "1";
            if (data.suggest_expired) {
                this.state.reason = "expired";
                this.state.reusableQty = "0";
            } else {
                this.state.reusableQty = data.tracking === "serial" ? "1" : "1";
            }
            if (data.tracking === "serial") {
                this.state.returnedQty = "1";
                this.state.reusableQty = this.state.reason === "expired" ? "0" : "1";
            }
            this.state.step = "reason";
            this.state.statusHint = _t("Choose the reason, then scan the replacement");
        } catch (error) {
            this.state.productId = false;
            this.state.productName = "";
            this.state.error =
                error?.data?.message || error?.message || _t("Lot lookup failed.");
            this.state.statusHint = _t("Scan the returned lot / serial");
        } finally {
            this.state.busy = false;
        }
    }

    async resolveReplacementLot({ autoConfirm = false } = {}) {
        const lotName = (this.state.replacementLotName || "").trim();
        if (!lotName) {
            this.state.error = _t("Scan the replacement lot / serial.");
            return;
        }
        if (!this.state.productId) {
            this.state.error = _t("Scan the returned item first.");
            return;
        }
        this.state.busy = true;
        this.state.error = "";
        try {
            const data = await this.pos.data.call("pos.exchange", "lookup_lot_for_pos", [
                lotName,
                this.pos.config.id,
                "replacement",
            ]);
            if (data.product_id !== this.state.productId) {
                throw new Error(
                    _t("Replacement must be the same product (%s).", this.state.productName)
                );
            }
            this.state.availableFgQty = data.available_fg_qty;
            this.state.step = "replacement";
            this.state.statusHint = _t("Ready — confirm exchange");
            if (autoConfirm) {
                await this.confirm();
            }
        } catch (error) {
            this.state.error =
                error?.data?.message || error?.message || _t("Replacement lookup failed.");
            this.state.statusHint = _t("Scan a Finished Goods lot / serial");
        } finally {
            this.state.busy = false;
        }
    }

    onReturnedQtyInput(ev) {
        this.state.returnedQty = ev.target.value;
        if (this.state.reason === "packaging_damage" && this.state.tracking === "lot") {
            this.state.reusableQty = this.state.returnedQty;
        }
    }

    onReusableQtyInput(ev) {
        this.state.reusableQty = ev.target.value;
    }

    async confirm() {
        this.state.error = "";
        if (!this.state.productId) {
            await this.resolveOriginLot();
            if (!this.state.productId) {
                return;
            }
        }
        const returnedQty = parseFloat(this.state.returnedQty);
        let reusableQty =
            this.state.reason === "expired" ? 0 : parseFloat(this.state.reusableQty);
        if (this.state.tracking === "serial") {
            // enforced server-side too
        }
        if (Number.isNaN(returnedQty) || returnedQty <= 0) {
            this.state.error = _t("Returned quantity must be positive.");
            return;
        }
        if (Number.isNaN(reusableQty) || reusableQty < 0 || reusableQty > returnedQty) {
            this.state.error = _t("Reusable quantity is invalid.");
            return;
        }
        if (this.state.tracking !== "none" && !(this.state.replacementLotName || "").trim()) {
            this.state.error = _t("Scan the replacement lot / serial.");
            this.replacementInputRef.el?.focus();
            return;
        }

        this.state.busy = true;
        this.state.step = "confirming";
        try {
            const partnerId =
                this.props.partnerId || this.pos.getOrder()?.getPartner()?.id || false;
            const result = await this.pos.data.call("pos.exchange", "create_from_pos", [
                {
                    session_id: this.pos.session.id,
                    origin_lot_name: (this.state.originLotName || "").trim(),
                    replacement_lot_name: (this.state.replacementLotName || "").trim(),
                    reason: this.state.reason,
                    returned_qty: returnedQty,
                    reusable_qty: reusableQty,
                    note: (this.state.note || "").trim(),
                    partner_id: partnerId,
                    origin_order_line_id: this.state.originOrderLineId || false,
                },
            ]);
            this.notification.add(
                _t("Exchange %s done — no cash movement.", result.exchange_name),
                { type: "success" }
            );
            this.props.getPayload?.(result);
            this.props.close();
        } catch (error) {
            this.state.error =
                error?.data?.message || error?.message || _t("Exchange failed.");
            this.state.step = "replacement";
            this.state.statusHint = _t("Fix the issue and try again");
        } finally {
            this.state.busy = false;
        }
    }

    resetOrigin() {
        this.state.productId = false;
        this.state.productName = "";
        this.state.originLotName = "";
        this.state.replacementLotName = "";
        this.state.step = "origin";
        this.state.statusHint = _t("Scan the returned lot / serial");
        this.state.error = "";
        setTimeout(() => this.originInputRef.el?.focus(), 50);
    }

    cancel() {
        this.props.close();
    }
}
