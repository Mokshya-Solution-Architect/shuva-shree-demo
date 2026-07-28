# -*- coding: utf-8 -*-
{
    'name': 'Nepali Calendar (Bikram Sambat)',
    'version': '19.0.2.0.1',
    'category': 'Tools',
    'summary': 'Toggle between Gregorian (A.D.) and Bikram Sambat (B.S.) calendars with Unicode support',
    'description': """
        Nepali Calendar Integration for Odoo 19
        ========================================
        * Toggle between A.D. and B.S. calendars in date picker
        * Unicode support for Nepali numerals (०-९) and month names (बैशाख, जेठ, etc.)
        * Multiple date format options (YYYY-MM-DD, DD MMMM YYYY, etc.)
        * Extended conversion capabilities with date arithmetic
        * Date validation and comparison utilities
        * User preference storage for calendar mode and Unicode display
        * Works with all Odoo date fields
        * Parse dates in Nepali numerals
        * Calculate date differences and add/subtract days
        * Current BS date with full weekday support

        New Features in v2.0.0:
        * Nepali numerals display (२०८१-०८-१५)
        * Nepali month names (कार्तिक, मंसिर, etc.)
        * Nepali weekday names (आइतबार, सोमबार, etc.)
        * Custom formatting with multiple format options
        * Date arithmetic (add days, calculate difference)
        * Date parsing and validation
        * Unicode toggle button in calendar UI
        * Enhanced date converter with 15+ utility functions
    """,
    'author': 'MSA',
    'depends': ['web', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'report/nepali_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '19_nepali_calendar/static/src/js/nepali_date_converter.js',
            '19_nepali_calendar/static/src/js/nepali_calendar_service.js',
            '19_nepali_calendar/static/src/js/nepali_datepicker_settings.js',
            '19_nepali_calendar/static/src/js/nepali_date_field_settings.js',
            '19_nepali_calendar/static/src/js/nepali_date_field_enhanced.js',
            '19_nepali_calendar/static/src/scss/nepali_datepicker.scss',
            '19_nepali_calendar/static/src/xml/nepali_datepicker.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
