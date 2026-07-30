/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { _t } from "@web/core/l10n/translation";
import {
    logConsignment,
    snapshotOrder,
    snapshotPosContext,
} from "@msa_pos_consignment/app/utils/consignment_debug";

/**
 * After settlement payment, open a resale order pre-filled with good-return
 * lines (new lots in Consignment Returns staging). Cashier can add fresh
 * warehouse products before collecting payment.
 */
export async function createConsignmentResaleOrder(pos, result) {
    const resaleLines = result.resale_lines || [];
    if (!resaleLines.length) {
        return null;
    }

    const newOrder = pos.addNewOrder();
    if (result.partner_id) {
        const partner = pos.models["res.partner"].get(result.partner_id);
        if (partner) {
            newOrder.setPartner(partner);
        }
    }
    newOrder.is_consignment_resale = true;
    if (result.consignment_id) {
        const consignment = pos.models["pos.consignment"]?.get(result.consignment_id);
        newOrder.consignment_id = consignment || result.consignment_id;
    }

    for (const resaleLine of resaleLines) {
        const product = pos.models["product.product"].get(resaleLine.product_id);
        if (!product) {
            continue;
        }
        const baseUom = product.uom_id;
        await pos.addLineToCurrentOrder(
            {
                product_id: product,
                product_tmpl_id: product.product_tmpl_id,
                product_uom_id: baseUom,
                qty: resaleLine.qty,
                price_unit: resaleLine.price_unit,
            },
            { merge: false },
            false
        );
        const line = newOrder.getLastOrderline?.() || newOrder.lines.at(-1);
        if (!line) {
            continue;
        }
        line.is_consignment_return = true;
        if (resaleLine.lot_id) {
            line.consignment_return_lot_id = resaleLine.lot_id;
        }
        if (resaleLine.lot_name && product.tracking !== "none") {
            line.setPackLotLines({
                modifiedPackLotLines: {},
                newPackLotLines: [{ lot_name: resaleLine.lot_name }],
                setQuantity: false,
            });
        }
    }

    pos.setOrder(newOrder);
    logConsignment("createConsignmentResaleOrder", "created", {
        order: snapshotOrder(newOrder),
        context: snapshotPosContext(pos),
    });
    return newOrder;
}

patch(PosStore.prototype, {
    async setup(env, deps) {
        const result = await super.setup(env, deps);
        this.pendingConsignmentResale = null;
        logConsignment("PosStore.setup", "POS store ready", snapshotPosContext(this));
        if (navigator.serviceWorker) {
            navigator.serviceWorker.getRegistration("/pos/service-worker.js").then((reg) => {
                logConsignment("PosStore.setup", "service worker state", {
                    registered: Boolean(reg),
                    active: Boolean(reg?.active),
                    waiting: Boolean(reg?.waiting),
                    installing: Boolean(reg?.installing),
                    scope: reg?.scope ?? null,
                });
            });
        }
        return result;
    },

    navigate(routeName, routeParams = {}) {
        logConsignment("PosStore.navigate", "BEFORE", {
            routeName,
            routeParams,
            pathname: window.location.pathname,
            context: snapshotPosContext(this),
            order: snapshotOrder(this.getOrder()),
        });
        const result = super.navigate(routeName, routeParams);
        logConsignment("PosStore.navigate", "AFTER", {
            routeName,
            routeParams,
            pathname: window.location.pathname,
            context: snapshotPosContext(this),
            order: snapshotOrder(this.getOrder()),
        });
        return result;
    },

    addNewOrder(data = {}) {
        logConsignment("PosStore.addNewOrder", "BEFORE", {
            data,
            context: snapshotPosContext(this),
        });
        const order = super.addNewOrder(data);
        logConsignment("PosStore.addNewOrder", "AFTER", {
            order: snapshotOrder(order),
            context: snapshotPosContext(this),
        });
        return order;
    },

    setOrder(order) {
        logConsignment("PosStore.setOrder", "switch", {
            from: snapshotOrder(this.getOrder()),
            to: snapshotOrder(order),
            pathname: window.location.pathname,
        });
        return super.setOrder(order);
    },
});

patch(OrderPaymentValidation.prototype, {
    async afterOrderValidation() {
        await super.afterOrderValidation(...arguments);
        const order = this.order;
        const pending = this.pos.pendingConsignmentResale;
        if (
            order?.is_consignment_settlement &&
            pending?.resale_lines?.length
        ) {
            this.pos.pendingConsignmentResale = null;
            await createConsignmentResaleOrder(this.pos, pending);
            this.pos.notification.add(
                _t(
                    "Good-return stock loaded — add fresh products if needed, then collect resale payment."
                ),
                { type: "info" }
            );
            this.pos.navigate("ProductScreen");
        }
    },
});

if (typeof window !== "undefined") {
    logConsignment("boot", "module loaded", {
        pathname: window.location.pathname,
        href: window.location.href,
        online: navigator.onLine,
    });
    window.addEventListener("beforeunload", () => {
        logConsignment("boot", "page beforeunload", {
            pathname: window.location.pathname,
        });
    });
}
