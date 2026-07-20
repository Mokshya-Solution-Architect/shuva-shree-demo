# Auto Scrap Location
 
**Version:** 19.0.0.0  
**Author:** Mokshya Solution Architect  
**Website:** https://www.mokshyasolution.com  
**Category:** Inventory  
**License:** LGPL-3
 
## Summary
 
Automatically sets default scrap location for stock scraps
 
## Features
 
- Auto-fills Scrap Location field
- Uses predefined 'Scrap Location'

## Dependencies
 
- `base`
- `stock`

## Test Cases
 
- Opened a new Scrap form (Inventory → Operations → Scrap → New) and verified the Scrap Location field is automatically pre-filled with 'Scrap Location'.
- Verified fallback to Odoo default ('Inventory Adjustment') when 'Scrap Location' does not exist in the database.


 