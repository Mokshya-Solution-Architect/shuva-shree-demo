# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NepaliDateMixin(models.AbstractModel):
    """
    Mixin to add automatic B.S date formatting to models

    Usage:
        class YourModel(models.Model):
            _name = 'your.model'
            _inherit = ['nepali.date.mixin']

            date_field = fields.Date('Date')
            datetime_field = fields.Datetime('DateTime')

    This will automatically add computed fields:
        - date_field_bs (for date fields)
        - datetime_field_bs (for datetime fields)
    """
    _name = 'nepali.date.mixin'
    _description = 'Nepali Date Formatting Mixin'

    def _get_nepali_config(self):
        """Get Nepali calendar configuration from system parameters"""
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        return {
            'enabled': IrConfigParameter.get_param('nepali_calendar.enable', default='False') == 'True',
            'date_format': IrConfigParameter.get_param('nepali_calendar.date_format', default='ad_only'),
            'date_pattern': IrConfigParameter.get_param('nepali_calendar.date_pattern', default='YYYY-MM-DD'),
            'datetime_format': IrConfigParameter.get_param('nepali_calendar.datetime_format', default='ad_only'),
            'show_in_reports': IrConfigParameter.get_param('nepali_calendar.show_in_reports', default='False') == 'True',
        }

    def format_date_bs(self, date_value):
        """
        Format a date value according to Nepali calendar settings

        Args:
            date_value: Date or datetime value

        Returns:
            Formatted string according to settings
        """
        if not date_value:
            return ''

        config = self._get_nepali_config()

        if not config['enabled'] or config['date_format'] == 'ad_only':
            # Return standard format
            if isinstance(date_value, str):
                return date_value
            return date_value.strftime('%Y-%m-%d')

        helper = self.env['nepali.date.helper']
        date_format = config['date_format']
        pattern = config['date_pattern']

        if date_format == 'bs_english':
            # B.S in English
            return helper.format_bs_date(date_value, format_str=pattern, use_unicode=False)

        elif date_format == 'bs_unicode':
            # B.S in Nepali Unicode
            return helper.format_bs_date(date_value, format_str=pattern, use_unicode=True)

        elif date_format == 'bs_ad_combined':
            # B.S + A.D Combined
            bs_date = helper.format_bs_date(date_value, format_str=pattern, use_unicode=False)
            ad_date = date_value.strftime('%Y-%m-%d') if hasattr(date_value, 'strftime') else str(date_value)
            return f"{bs_date} ({ad_date})"

        return str(date_value)

    def format_datetime_bs(self, datetime_value):
        """
        Format a datetime value according to Nepali calendar settings

        Args:
            datetime_value: Datetime value

        Returns:
            Formatted string according to settings
        """
        if not datetime_value:
            return ''

        config = self._get_nepali_config()

        if not config['enabled'] or config['datetime_format'] == 'ad_only':
            # Return standard format
            if isinstance(datetime_value, str):
                return datetime_value
            return datetime_value.strftime('%Y-%m-%d %H:%M:%S')

        helper = self.env['nepali.date.helper']
        datetime_format = config['datetime_format']
        pattern = config['date_pattern']

        if datetime_format == 'bs_english':
            # B.S in English with time
            return helper.format_bs_datetime(datetime_value, format_str=pattern, use_unicode=False)

        elif datetime_format == 'bs_unicode':
            # B.S in Nepali Unicode with time
            return helper.format_bs_datetime(datetime_value, format_str=pattern, use_unicode=True)

        elif datetime_format == 'bs_ad_combined':
            # B.S + A.D Combined with time
            bs_datetime = helper.format_bs_datetime(datetime_value, format_str=pattern, use_unicode=False)
            ad_datetime = datetime_value.strftime('%Y-%m-%d %H:%M:%S') if hasattr(datetime_value, 'strftime') else str(datetime_value)
            return f"{bs_datetime} ({ad_datetime})"

        return str(datetime_value)

    @api.model
    def _add_nepali_date_fields(self):
        """
        Automatically add B.S computed fields for date/datetime fields
        This should be called in _register_hook or after model definition
        """
        for field_name, field in self._fields.items():
            if isinstance(field, (fields.Date, fields.Datetime)) and not field_name.endswith('_bs'):
                bs_field_name = f"{field_name}_bs"

                # Skip if already exists
                if bs_field_name in self._fields:
                    continue

                # Determine compute method
                if isinstance(field, fields.Date):
                    compute_method = lambda self, fname=field_name: self._compute_bs_date(fname)
                else:
                    compute_method = lambda self, fname=field_name: self._compute_bs_datetime(fname)

                # Add computed field
                self._add_field(bs_field_name, fields.Char(
                    string=f"{field.string} (B.S)",
                    compute=compute_method,
                    store=False,
                ))

    def _compute_bs_date(self, field_name):
        """Compute B.S date field"""
        bs_field_name = f"{field_name}_bs"
        for record in self:
            date_value = record[field_name]
            record[bs_field_name] = record.format_date_bs(date_value)

    def _compute_bs_datetime(self, field_name):
        """Compute B.S datetime field"""
        bs_field_name = f"{field_name}_bs"
        for record in self:
            datetime_value = record[field_name]
            record[bs_field_name] = record.format_datetime_bs(datetime_value)
