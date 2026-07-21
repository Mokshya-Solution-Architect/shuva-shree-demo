/** @odoo-module **/
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { Orderline } from "@point_of_sale/app/components/orderline/orderline";



function getAvailableUomsForLine(line) {
    const tmpl = line.product_id.product_tmpl_id;
    const baseUom = tmpl?.uom_id || line.product_id.uom_id;
    const packagingUoms = (tmpl?.uom_ids || []).filter(Boolean);
    return [baseUom, ...packagingUoms].filter(
        (u, idx, arr) => u && arr.findIndex((x) => x.id === u.id) === idx
    );
}



export class RemoveLineButton extends Component {
    static template = "msa_pos_uom.RemoveLineButton";
    static props = {
        line: Object,
    };

    onClick(event) {
        event.stopPropagation();
        this.props.line.order_id.removeOrderline(this.props.line);
    }
}



export class UomInlineButton extends Component {
    static template = "msa_pos_uom.UomInlineButton";
    static props = {
        line: Object,
    };

    setup() {
        this.dialog = useService("dialog");
    }

    get currentUomName() {
        const line = this.props.line;
        return (line.product_uom_id || line.product_id.uom_id)?.name || _t("Unit");
    }

    get isClickable() {
        return getAvailableUomsForLine(this.props.line).length > 1;
    }

    async onClick(event) {
        event.stopPropagation();
        const line = this.props.line;
        const allUoms = getAvailableUomsForLine(line);
        if (allUoms.length <= 1) {
            return;
        }
        const currentUom = line.product_uom_id || line.product_id.uom_id;
        const uomList = allUoms.map((uom) => ({
            id: uom.id,
            label: uom.name,
            isSelected: uom.id === currentUom?.id,
            item: uom,
        }));
        const selectedUom = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Select Unit of Measure"),
            list: uomList,
        });
        if (selectedUom) {
            line.setUom(selectedUom);
        }
    }
}

Orderline.components = {
    ...Orderline.components,
    UomInlineButton,
    RemoveLineButton,
};



export class UomSelectorButton extends Component {
    static template = "msa_pos_uom.UomSelectorButton";
    static props = {
        class: { type: String, optional: true },
    };

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }

    get selectedLine() {
        return this.pos.getOrder()?.getSelectedOrderline();
    }

    get availableUoms() {
        const line = this.selectedLine;
        if (!line) {
            return [];
        }
        const currentUom = line.product_uom_id || line.product_id.uom_id;
        return getAvailableUomsForLine(line).map((uom) => ({
            id: uom.id,
            label: uom.name,
            isSelected: uom.id === currentUom?.id,
            item: uom,
        }));
    }

    get isVisible() {
        return this.availableUoms.length > 1;
    }

    get currentUomName() {
        const line = this.selectedLine;
        if (!line) {
            return _t("Unit");
        }
        return (line.product_uom_id || line.product_id.uom_id)?.name || _t("Unit");
    }

    async onClick() {
        const line = this.selectedLine;
        if (!line || this.availableUoms.length <= 1) {
            return;
        }
        const selectedUom = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Select Unit of Measure"),
            list: this.availableUoms,
        });
        if (selectedUom) {
            line.setUom(selectedUom);
        }
    }
}



ControlButtons.components = {
    ...ControlButtons.components,
    UomSelectorButton,
};
