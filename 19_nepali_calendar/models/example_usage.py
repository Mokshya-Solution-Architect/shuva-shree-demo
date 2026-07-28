# -*- coding: utf-8 -*-
"""
Example: How to use Nepali Date Mixin in your models

This is a reference implementation showing how to integrate
Nepali calendar features into your custom models.
"""

from odoo import models, fields, api


class ExampleNepaliDateModel(models.Model):
    """
    Example model demonstrating Nepali date integration

    This model shows how to:
    1. Inherit the nepali.date.mixin
    2. Use standard date/datetime fields
    3. Add computed B.S date fields
    4. Display both A.D and B.S dates in views
    """
    _name = 'example.nepali.date'
    _description = 'Example Model with Nepali Date Support'
    _inherit = ['nepali.date.mixin']

    name = fields.Char('Name', required=True)

    # Standard date fields (stored in A.D.)
    event_date = fields.Date('Event Date')
    created_datetime = fields.Datetime('Created DateTime', default=fields.Datetime.now)

    # Computed B.S fields (automatically formatted based on settings)
    event_date_bs = fields.Char('Event Date (B.S)', compute='_compute_event_date_bs', store=False)
    created_datetime_bs = fields.Char('Created DateTime (B.S)', compute='_compute_created_datetime_bs', store=False)

    @api.depends('event_date')
    def _compute_event_date_bs(self):
        """Compute B.S representation of event date"""
        for record in self:
            record.event_date_bs = record.format_date_bs(record.event_date)

    @api.depends('created_datetime')
    def _compute_created_datetime_bs(self):
        """Compute B.S representation of created datetime"""
        for record in self:
            record.created_datetime_bs = record.format_datetime_bs(record.created_datetime)


# ============================================================================
# EXAMPLE: How to add B.S date fields to existing Odoo models
# ============================================================================

# Example 1: Adding B.S date to Sale Orders
"""
class SaleOrder(models.Model):
    _inherit = ['sale.order', 'nepali.date.mixin']

    # Add computed B.S date field
    date_order_bs = fields.Char(
        'Order Date (B.S)',
        compute='_compute_date_order_bs',
        store=False
    )

    @api.depends('date_order')
    def _compute_date_order_bs(self):
        for order in self:
            order.date_order_bs = order.format_date_bs(order.date_order)
"""

# Example 2: Adding B.S date to HR Employee
"""
class HrEmployee(models.Model):
    _inherit = ['hr.employee', 'nepali.date.mixin']

    # Add computed B.S fields for existing date fields
    birthday_bs = fields.Char('Birthday (B.S)', compute='_compute_birthday_bs')
    joining_date_bs = fields.Char('Joining Date (B.S)', compute='_compute_joining_date_bs')

    @api.depends('birthday')
    def _compute_birthday_bs(self):
        for employee in self:
            employee.birthday_bs = employee.format_date_bs(employee.birthday)

    @api.depends('joining_date')
    def _compute_joining_date_bs(self):
        for employee in self:
            employee.joining_date_bs = employee.format_date_bs(employee.joining_date)
"""

# Example 3: Using in reports (QWeb)
"""
In your QWeb report template, you can access the nepali.date.helper:

<template id="report_invoice_document">
    <t t-set="helper" t-value="env['nepali.date.helper']"/>

    <!-- Display invoice date in B.S -->
    <div class="row">
        <div class="col-6">
            <strong>Invoice Date:</strong>
            <span t-field="o.invoice_date"/>
        </div>
        <div class="col-6">
            <strong>Invoice Date (B.S):</strong>
            <t t-esc="helper.format_bs_date(o.invoice_date, 'YYYY MMMM DD', False)"/>
        </div>
    </div>
</template>
"""

# Example 4: Using in Python code
"""
# Get helper
helper = self.env['nepali.date.helper']

# Convert AD to BS
from datetime import date
ad_date = date(2024, 11, 27)
bs_dict = helper.ad_to_bs(ad_date)
# Returns: {'year': 2081, 'month': 8, 'day': 12}

# Format as string
bs_date_english = helper.format_bs_date(ad_date, 'YYYY-MM-DD', use_unicode=False)
# Returns: "2081-08-12"

bs_date_nepali = helper.format_bs_date(ad_date, 'YYYY MMMM DD', use_unicode=True)
# Returns: "२०८१ कार्तिक १२"

# Format datetime
from datetime import datetime
ad_datetime = datetime(2024, 11, 27, 14, 30, 0)
bs_datetime = helper.format_bs_datetime(ad_datetime, 'YYYY-MM-DD', use_unicode=False)
# Returns: "2081-08-12 14:30"
"""
