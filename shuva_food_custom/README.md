# Shuva Food Custom Workflows for Odoo 19 Enterprise

This module is built for the Shuva Shree food manufacturing requirement where standard Odoo is used first and custom code only fills the gaps.

## Covers

- Alt Unit / Pack Count fields on Purchase, Sale, Stock Moves and Manufacturing.
- Pack Type master: Bora, Jar, Jumbo, Carton, etc.
- Unique pack/lot barcode generation for raw material physical packs.
- Finished goods jumbo/carton lot generation from Manufacturing Orders.
- Lot fields for pack barcode, pack type, pack quantity, supplier, purchase and MO traceability.
- Return reason master for normal, expiry, breakage and repack returns.
- Pack barcode history report.
- MRP planned-vs-actual consumption variance report.
- POS pack barcode JS starter patch.

## Standard Odoo still handles

- Purchase Order, Receipt, Vendor Bill
- Lots/Serial Numbers and Expiration Dates
- Manufacturing Order and Flexible BOM consumption
- POS standard sales
- Reverse transfer / returns
- Credit notes and payments
- Inventory valuation and accounting

## Important installation notes

1. Install required standard apps first: Inventory, Purchase, Sales, Manufacturing, POS, Accounting, Barcode.
2. Copy this folder into your custom addons path.
3. Restart Odoo and upgrade the Apps list.
4. Install `Shuva Food Custom Workflows`.
5. Create Pack Types: `BORA`, `JAR`, `JUMBO`, `CARTON`.
6. Enable lot tracking on all products requiring physical pack barcodes.
7. Set product fields under Inventory tab: Require Unique Pack Barcode, Default Pack Type, Default Qty per Pack, POS Qty When Pack Barcode Scanned.

## Note about POS

Odoo POS frontend APIs can change between major versions. The backend lookup method is stable in this module. If the Odoo 19 POS barcode service uses a different hook name in your exact build, only `static/src/js/pos_lot_barcode.js` needs adjustment.
