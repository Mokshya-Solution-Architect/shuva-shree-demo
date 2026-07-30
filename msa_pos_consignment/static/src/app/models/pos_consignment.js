/** @odoo-module **/

/**
 * This file is intentionally minimal.
 *
 * pos.consignment and pos.consignment.line records are loaded into the POS
 * data service automatically via _load_pos_data_models / _load_pos_data_fields
 * on the Python side (when enable_consignment = True on the POS config).
 *
 * Accessing them in JS:
 *   this.pos.models['pos.consignment'].getAll()
 *   this.pos.models['pos.consignment'].filter(c => c.partner_id?.id === partnerId)
 *
 * No custom class definition is required for basic many2one / one2many navigation
 * because the POS data service handles relationship wiring automatically for
 * all loaded models.
 */
