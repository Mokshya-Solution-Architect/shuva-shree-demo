# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class NepaliCalendarController(http.Controller):

    @http.route('/nepali_calendar/get_settings', type='json', auth='user')
    def get_settings(self):
        """Get Nepali calendar settings for the current user"""
        IrConfigParameter = request.env['ir.config_parameter'].sudo()

        settings = {
            'enable': IrConfigParameter.get_param('nepali_calendar.enable', default='False') == 'True',
            'date_format': IrConfigParameter.get_param('nepali_calendar.date_format', default='ad_only'),
            'date_pattern': IrConfigParameter.get_param('nepali_calendar.date_pattern', default='YYYY-MM-DD'),
            'datetime_format': IrConfigParameter.get_param('nepali_calendar.datetime_format', default='ad_only'),
            'calendar_mode': IrConfigParameter.get_param('nepali_calendar.calendar_mode', default='ad'),
            'show_in_reports': IrConfigParameter.get_param('nepali_calendar.show_in_reports', default='False') == 'True',
        }

        return settings
