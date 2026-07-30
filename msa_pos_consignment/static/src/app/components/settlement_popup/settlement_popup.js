/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useAsyncLockedMethod } from "@point_of_sale/app/hooks/hooks";
import { createConsignmentResaleOrder } from "@msa_pos_consignment/app/models/pos_store_consignment";

/**
 * SettlementPopup — per-line qty breakdown for a dispatched consignment.
 * Quantities are entered in base UoM (Pcs). Good returns receive new lots
 * at settlement and are resold in a follow-up POS order.
 */
export class SettlementPopup extends Component {
    static template = "msa_pos_consignment.SettlementPopup";
    static components = { Dialog };
    static props = {
        close: Function,
        getPayload: { type: Function, optional: true },
        consignment: Object,
        partnerId: [Number, Boolean],
        partnerName: String,
    };

    setup() {
        this.pos = usePos();
        this.notification = useService("notification");
        const c = this.props.consignment;
        this.state = useState({
            busy: false,
            error: "",
            lines: (c.lines || []).map((l) => this._mapLine(l)),
        });
        this.confirm = useAsyncLockedMethod(this.confirm);
    }

    get isSmallScreen() {
        return this.pos.isSmallProductScreen;
    }

    get dialogSize() {
        return this.isSmallScreen ? "fs" : "lg";
    }

    _mapLine(l) {
        const qtyBase = l.qty_dispatched_base ?? l.qty_dispatched;
        const baseUomName = l.base_uom_name || l.uom_name || "";
        return {
            line_id: l.id,
            product_id: l.product_id,
            product_name: l.product_name,
            dispatch_uom_name: l.uom_name || "",
            qty_dispatched: l.qty_dispatched,
            base_uom_name: baseUomName,
            qty_dispatched_base: qtyBase,
            price_unit_base: l.price_unit_base ?? l.price_unit,
            qty_sold: String(qtyBase),
            qty_returned_good: "0",
            qty_returned_scrap: "0",
        };
    }

    get consignmentName() {
        return this.props.consignment.name;
    }

    formatAmount(amount) {
        const currency = this.pos.currency;
        if (!currency) return String(amount);
        return currency.symbol + " " + Number(amount).toFixed(currency.decimal_places || 2);
    }

    formatDispatched(line) {
        if (!line.dispatch_uom_name || line.dispatch_uom_name === line.base_uom_name) {
            return `${line.qty_dispatched} ${line.base_uom_name}`;
        }
        return `${line.qty_dispatched} ${line.dispatch_uom_name} (${line.qty_dispatched_base} ${line.base_uom_name})`;
    }

    lineBalance(line) {
        const sold = parseFloat(line.qty_sold) || 0;
        const good = parseFloat(line.qty_returned_good) || 0;
        const scrap = parseFloat(line.qty_returned_scrap) || 0;
        return Number((line.qty_dispatched_base - sold - good - scrap).toFixed(6));
    }

    lineIsBalanced(line) {
        return Math.abs(this.lineBalance(line)) < 0.000001;
    }

    get allBalanced() {
        return this.state.lines.every((l) => this.lineIsBalanced(l));
    }

    get canConfirm() {
        return !this.state.busy && this.allBalanced;
    }

    get settlementTotal() {
        return this.state.lines.reduce((sum, l) => {
            return sum + (parseFloat(l.qty_sold) || 0) * l.price_unit_base;
        }, 0);
    }

    onQtyInput(line, field, ev) {
        line[field] = ev.target.value;
    }

    autoBalance(line) {
        const good = parseFloat(line.qty_returned_good) || 0;
        const scrap = parseFloat(line.qty_returned_scrap) || 0;
        const sold = line.qty_dispatched_base - good - scrap;
        line.qty_sold = String(Math.max(0, sold));
    }

    async confirm() {
        this.state.error = "";
        if (!this.allBalanced) {
            this.state.error = _t(
                "All quantities must balance (Sold + Good returns + Scrap = Dispatched)."
            );
            return;
        }

        this.state.busy = true;
        try {
            const linesPayload = this.state.lines.map((l) => ({
                line_id: l.line_id,
                qty_sold: parseFloat(l.qty_sold) || 0,
                qty_returned_good: parseFloat(l.qty_returned_good) || 0,
                qty_returned_scrap: parseFloat(l.qty_returned_scrap) || 0,
            }));

            const result = await this.pos.data.call(
                "pos.consignment",
                "action_settle",
                [
                    this.props.consignment.id,
                    { session_id: this.pos.session.id, lines: linesPayload },
                ]
            );

            const hasSold = result.sold_lines?.length > 0;
            const hasResale = result.resale_lines?.length > 0;

            if (hasSold) {
                if (hasResale) {
                    this.pos.pendingConsignmentResale = result;
                }
                await this._createSettlementOrder(result);
            } else if (hasResale) {
                await createConsignmentResaleOrder(this.pos, result);
                this.notification.add(
                    _t(
                        "Settlement %(ref)s complete — good-return stock loaded. Add fresh products if needed, then collect payment.",
                        { ref: result.consignment_name }
                    ),
                    { type: "success" }
                );
                this.pos.navigate("ProductScreen");
            } else {
                this.notification.add(
                    _t("Settlement %(ref)s complete.", { ref: result.consignment_name }),
                    { type: "success" }
                );
            }

            this.props.getPayload?.(result);
            this.props.close();
        } catch (error) {
            this.state.error =
                error?.data?.message || error?.message || _t("Settlement failed.");
        } finally {
            this.state.busy = false;
        }
    }

    async _createSettlementOrder(result) {
        const newOrder = this.pos.addNewOrder();
        if (result.partner_id) {
            const partner = this.pos.models["res.partner"].get(result.partner_id);
            if (partner) {
                newOrder.setPartner(partner);
            }
        }
        newOrder.is_consignment_settlement = true;
        if (result.consignment_id) {
            const consignment = this.pos.models["pos.consignment"]?.get(result.consignment_id);
            newOrder.consignment_id = consignment || result.consignment_id;
        }

        for (const soldLine of result.sold_lines) {
            const product = this.pos.models["product.product"].get(soldLine.product_id);
            if (!product) {
                continue;
            }
            await this.pos.addLineToCurrentOrder(
                {
                    product_id: product,
                    product_tmpl_id: product.product_tmpl_id,
                    product_uom_id: product.uom_id,
                    qty: soldLine.qty,
                    price_unit: soldLine.price_unit,
                },
                { merge: false },
                false
            );
        }

        this.pos.setOrder(newOrder);
        this.pos.navigate("PaymentScreen", { orderUuid: newOrder.uuid });
        this.notification.add(
            _t(
                "Settlement %(ref)s — collect %(amount)s for sold items.",
                {
                    ref: result.consignment_name,
                    amount:
                        (this.pos.currency?.symbol || "") +
                        " " +
                        Number(result.amount_to_collect).toFixed(2),
                }
            ),
            { type: "success" }
        );
    }

    cancel() {
        this.props.close();
    }
}
