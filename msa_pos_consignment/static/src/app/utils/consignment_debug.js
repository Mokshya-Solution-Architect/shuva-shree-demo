/** @odoo-module **/

/**
 * Toggle at runtime in the browser console:
 *   localStorage.setItem('msa_pos_consignment_debug', '1')
 *   localStorage.removeItem('msa_pos_consignment_debug')
 */
const DEBUG_KEY = "msa_pos_consignment_debug";

export function isConsignmentDebugEnabled() {
    try {
        return localStorage.getItem(DEBUG_KEY) === "1";
    } catch {
        return false;
    }
}

export function logConsignment(scope, message, data) {
    if (!isConsignmentDebugEnabled()) {
        return;
    }
    const prefix = `[msa_pos_consignment:${scope}]`;
    if (data !== undefined) {
        console.debug(prefix, message, data);
    } else {
        console.debug(prefix, message);
    }
}

export function warnConsignment(scope, message, data) {
    const prefix = `[msa_pos_consignment:${scope}]`;
    if (data !== undefined) {
        console.warn(prefix, message, data);
    } else {
        console.warn(prefix, message);
    }
}

export function errorConsignment(scope, message, data) {
    const prefix = `[msa_pos_consignment:${scope}]`;
    if (data !== undefined) {
        console.error(prefix, message, data);
    } else {
        console.error(prefix, message);
    }
}

/** Snapshot useful POS/order fields for logs (never throws). */
export function snapshotOrder(order) {
    if (!order) {
        return null;
    }
    try {
        return {
            uuid: order.uuid,
            partner_id: order.partner_id?.id ?? null,
            partner_name: order.partner_id?.name ?? null,
            line_count: order.lines?.length ?? 0,
            isEmpty: order.isEmpty?.(),
            is_consignment_dispatch: order.uiState?.is_consignment_dispatch ?? false,
            pos_reference: order.pos_reference,
        };
    } catch (e) {
        return { uuid: order.uuid, snapshot_error: String(e) };
    }
}

export function snapshotPosContext(pos) {
    try {
        return {
            selectedOrderUuid: pos.selectedOrderUuid,
            router_current: pos.router?.state?.current ?? null,
            pathname: window.location.pathname,
            online: navigator.onLine,
            session_id: pos.session?.id ?? null,
            config_id: pos.config?.id ?? null,
            enable_consignment: pos.config?.enable_consignment ?? false,
            open_orders: pos.models?.["pos.order"]?.getAll?.()?.length ?? 0,
        };
    } catch (e) {
        return { snapshot_error: String(e), pathname: window.location.pathname };
    }
}
