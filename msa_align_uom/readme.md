# Align UOM in Barcode, Picking and Pick Slip

**Version:** 19.0.0.0  
**Author:** Mokshya Solution Architect  
**Website:** https://www.mokshyasolution.com  
**Category:** Inventory  
**License:** LGPL-3
 
## Summary
 
Aligns the Unit of Measure (UOM) from confirmed Sales Orders and Purchase Orders across Barcode App, Inventory Pickings, and Pick Slip reports, ensuring warehouse operations use the same UOM as the originating order lines.
 
## Features
 
- Aligns the Unit of Measure (UOM) from confirmed Sales Orders and Purchase Orders
- Displays the same UOM in the Barcode App
- Displays the same UOM in Inventory Pickings
- Displays the same UOM on Pick Slip reports
- Reduces confusion caused by automatic UOM conversions during picking and delivery

## Dependencies
 
- `base`
- `stock`
- `sale_management`
- `purchase`
- `barcodes`

## Test Cases

- Created a Sales Order using a product with a specific UOM and confirmed the order.
- Verified that the generated Delivery Order displays the same UOM as the Sales Order line.
- Opened the Barcode App and verified that the UOM shown matches the confirmed Sales Order.
- Printed the Pick Slip and verified that the displayed UOM matches the Sales Order line.
- Created a Purchase Order using a product with a specific UOM and confirmed the order.
- Verified that the generated Receipt displays the same UOM as the Purchase Order line.
- Opened the Barcode App for the Receipt operation and confirmed that the UOM is displayed correctly.
- Printed the Pick Slip/Receipt document and verified UOM consistency across all warehouse documents.

 
