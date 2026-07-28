# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Date format selection
    nepali_date_format = fields.Selection([
        ('ad_only', 'A.D Only (Default)'),
        ('bs_english', 'B.S in English (e.g., 2081-08-15)'),
        ('bs_unicode', 'B.S in Nepali Unicode (e.g., २०८१-०८-१५)'),
        ('bs_ad_combined', 'B.S + A.D Combined (e.g., 2081-08-15 (2024-11-27))'),
    ], string='Date Display Format',
    default='ad_only',
    config_parameter='nepali_calendar.date_format',
    help='Select how dates should be displayed throughout the system')

    # Date format pattern
    nepali_date_pattern = fields.Selection([
        ('YYYY-MM-DD', 'YYYY-MM-DD (2081-08-15)'),
        ('YYYY MMMM DD', 'YYYY MMMM DD (2081 Kartik 15)'),
        ('DD MMMM YYYY', 'DD MMMM YYYY (15 Kartik 2081)'),
    ], string='Date Pattern',
    default='YYYY-MM-DD',
    config_parameter='nepali_calendar.date_pattern',
    help='Pattern for formatting B.S dates')

    # Datetime format
    nepali_datetime_format = fields.Selection([
        ('ad_only', 'A.D Only (Default)'),
        ('bs_english', 'B.S in English with time'),
        ('bs_unicode', 'B.S in Nepali Unicode with time'),
        ('bs_ad_combined', 'B.S + A.D Combined with time'),
    ], string='DateTime Display Format',
    default='ad_only',
    config_parameter='nepali_calendar.datetime_format',
    help='Select how datetime fields should be displayed')

    # Calendar picker mode
    nepali_calendar_mode = fields.Selection([
        ('ad', 'A.D Calendar'),
        ('bs', 'B.S Calendar'),
        ('both', 'Both (A.D + B.S Toggle)'),
    ], string='Calendar Picker Mode',
    default='ad',
    config_parameter='nepali_calendar.calendar_mode',
    help='Select which calendar to show in date pickers')

    # Enable/Disable features
    enable_nepali_calendar = fields.Boolean(
        string='Enable Nepali Calendar Features',
        default=False,
        config_parameter='nepali_calendar.enable',
        help='Enable Nepali calendar features throughout the system'
    )

    show_bs_in_reports = fields.Boolean(
        string='Show B.S Dates in Reports',
        default=False,
        config_parameter='nepali_calendar.show_in_reports',
        help='Display B.S dates in printed reports and PDFs'
    )

    @api.onchange('enable_nepali_calendar')
    def _onchange_enable_nepali_calendar(self):
        """Reset format options when disabling Nepali calendar"""
        if not self.enable_nepali_calendar:
            self.nepali_date_format = 'ad_only'
            self.nepali_datetime_format = 'ad_only'
            self.nepali_calendar_mode = 'ad'
            self.show_bs_in_reports = False
