# -*- coding: utf-8 -*-
from odoo import models, api
from datetime import datetime, timedelta

class NepaliDateHelper(models.AbstractModel):
    _name = 'nepali.date.helper'
    _description = 'Nepali Date Conversion Helper for Reports'

    # BS calendar data: days in each month for years 2000-2100
    BS_CALENDAR_DATA = {
        2000: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2001: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2002: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2003: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2004: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2005: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2006: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2007: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2008: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 29, 31],
        2009: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2010: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2011: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2012: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2013: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2014: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2015: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2016: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2017: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2018: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2019: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2020: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2021: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2022: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2023: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2024: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2025: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2026: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2027: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2028: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2029: [31, 31, 32, 31, 32, 30, 30, 29, 30, 29, 30, 30],
        2030: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2031: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2032: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2033: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2034: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2035: [30, 32, 31, 32, 31, 31, 29, 30, 30, 29, 29, 31],
        2036: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2037: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2038: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2039: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2040: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2041: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2042: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2043: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2044: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2045: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2046: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2047: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2048: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2049: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2050: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2051: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2052: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2053: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2054: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2055: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2056: [31, 31, 32, 31, 32, 30, 30, 29, 30, 29, 30, 30],
        2057: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2058: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2059: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2060: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2061: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2062: [30, 32, 31, 32, 31, 31, 29, 30, 29, 30, 29, 31],
        2063: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2064: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2065: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2066: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 29, 31],
        2067: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2068: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2069: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2070: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2071: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2072: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2073: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2074: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2075: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2076: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2077: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2078: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2079: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2080: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2081: [31, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2082: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2083: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2084: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2085: [31, 32, 31, 32, 30, 31, 30, 30, 29, 30, 30, 30],
        2086: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2087: [31, 31, 32, 31, 31, 31, 30, 30, 29, 30, 30, 30],
        2088: [30, 31, 32, 32, 30, 31, 30, 30, 29, 30, 30, 30],
        2089: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2090: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2091: [31, 31, 32, 31, 31, 31, 30, 30, 29, 30, 30, 30],
        2092: [30, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2093: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2094: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2095: [31, 31, 32, 31, 31, 31, 30, 29, 30, 30, 30, 30],
        2096: [30, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2097: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2098: [31, 31, 32, 31, 31, 31, 29, 30, 29, 30, 30, 31],
        2099: [31, 31, 32, 31, 31, 31, 30, 29, 29, 30, 30, 30],
        2100: [31, 32, 31, 32, 30, 31, 30, 29, 30, 29, 30, 30],
    }

    # Reference date: 1943-04-14 AD = 2000-01-01 BS
    BS_REFERENCE_DATE = datetime(1943, 4, 14)
    BS_REFERENCE_YEAR = 2000
    BS_REFERENCE_MONTH = 1
    BS_REFERENCE_DAY = 1

    # Month names
    MONTH_NAMES_ENGLISH = [
        'Baisakh', 'Jestha', 'Ashar', 'Shrawan', 'Bhadra', 'Ashoj',
        'Kartik', 'Mangsir', 'Poush', 'Magh', 'Falgun', 'Chaitra'
    ]

    MONTH_NAMES_NEPALI = [
        'बैशाख', 'जेठ', 'असार', 'साउन', 'भदौ', 'असोज',
        'कार्तिक', 'मंसिर', 'पुष', 'माघ', 'फागुन', 'चैत'
    ]

    # Nepali numerals
    NEPALI_NUMERALS = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९']

    @api.model
    def _to_nepali_number(self, num):
        """Convert English number to Nepali numerals"""
        return ''.join(self.NEPALI_NUMERALS[int(d)] if d.isdigit() else d for d in str(num))

    @api.model
    def _count_days_from_reference(self, ad_date):
        """Count total days from reference date to given AD date"""
        if isinstance(ad_date, str):
            ad_date = datetime.strptime(ad_date[:10], '%Y-%m-%d')
        delta = ad_date - self.BS_REFERENCE_DATE
        return delta.days

    @api.model
    def ad_to_bs(self, ad_date):
        """
        Convert AD date to BS date
        Returns dict with keys: year, month, day
        """
        if not ad_date:
            return None

        try:
            # Convert to datetime if string
            if isinstance(ad_date, str):
                ad_date = datetime.strptime(ad_date[:10], '%Y-%m-%d')

            # Count days from reference
            total_days = self._count_days_from_reference(ad_date)

            # Start from reference BS date
            bs_year = self.BS_REFERENCE_YEAR
            bs_month = self.BS_REFERENCE_MONTH
            bs_day = self.BS_REFERENCE_DAY + total_days

            # Adjust year and month based on total days
            while bs_day > 0:
                if bs_year not in self.BS_CALENDAR_DATA:
                    return None

                days_in_month = self.BS_CALENDAR_DATA[bs_year][bs_month - 1]

                if bs_day <= days_in_month:
                    break

                bs_day -= days_in_month
                bs_month += 1

                if bs_month > 12:
                    bs_month = 1
                    bs_year += 1

            # Handle negative days
            while bs_day <= 0:
                bs_month -= 1
                if bs_month < 1:
                    bs_month = 12
                    bs_year -= 1

                if bs_year not in self.BS_CALENDAR_DATA:
                    return None

                days_in_month = self.BS_CALENDAR_DATA[bs_year][bs_month - 1]
                bs_day += days_in_month

            return {
                'year': bs_year,
                'month': bs_month,
                'day': bs_day
            }

        except Exception as e:
            return None

    @api.model
    def format_bs_date(self, ad_date, format_str='YYYY MMMM DD', use_unicode=False):
        """
        Format AD date as BS date string

        Args:
            ad_date: AD date (datetime, date, or string)
            format_str: Format pattern (default: 'YYYY MMMM DD')
            use_unicode: Use Nepali numerals (default: False)

        Returns:
            Formatted BS date string (e.g., "2082 Magh 6" or "२०८२ माघ ६")
        """
        if not ad_date:
            return ''

        try:
            bs_date = self.ad_to_bs(ad_date)
            if not bs_date:
                return ''

            year = bs_date['year']
            month = bs_date['month']
            day = bs_date['day']

            # Get month name
            month_name = self.MONTH_NAMES_NEPALI[month - 1] if use_unicode else self.MONTH_NAMES_ENGLISH[month - 1]

            # Format based on pattern
            if format_str == 'YYYY MMMM DD':
                # Example: 2082 Magh 6 or २०८२ माघ ६
                if use_unicode:
                    return f"{self._to_nepali_number(year)} {month_name} {self._to_nepali_number(day)}"
                else:
                    return f"{year} {month_name} {day}"

            elif format_str == 'YYYY-MM-DD':
                # Example: 2082-10-06 or २०८२-१०-०६
                month_str = str(month).zfill(2)
                day_str = str(day).zfill(2)
                if use_unicode:
                    return f"{self._to_nepali_number(year)}-{self._to_nepali_number(month_str)}-{self._to_nepali_number(day_str)}"
                else:
                    return f"{year}-{month_str}-{day_str}"

            elif format_str == 'DD MMMM YYYY':
                # Example: 6 Magh 2082 or ६ माघ २०८२
                if use_unicode:
                    return f"{self._to_nepali_number(day)} {month_name} {self._to_nepali_number(year)}"
                else:
                    return f"{day} {month_name} {year}"

            else:
                # Default fallback
                if use_unicode:
                    return f"{self._to_nepali_number(year)} {month_name} {self._to_nepali_number(day)}"
                else:
                    return f"{year} {month_name} {day}"

        except Exception as e:
            return ''

    @api.model
    def format_bs_datetime(self, ad_datetime, format_str='YYYY MMMM DD', use_unicode=False):
        """
        Format AD datetime as BS datetime string

        Args:
            ad_datetime: AD datetime (datetime or string)
            format_str: Format pattern (default: 'YYYY MMMM DD')
            use_unicode: Use Nepali numerals (default: False)

        Returns:
            Formatted BS datetime string (e.g., "2082 Magh 6 14:30" or "२०८२ माघ ६ १४:३०")
        """
        if not ad_datetime:
            return ''

        try:
            # Convert to datetime if string
            if isinstance(ad_datetime, str):
                ad_datetime = datetime.strptime(ad_datetime[:19], '%Y-%m-%d %H:%M:%S')

            # Get date part
            date_str = self.format_bs_date(ad_datetime, format_str, use_unicode)

            # Get time part
            hours = str(ad_datetime.hour).zfill(2)
            minutes = str(ad_datetime.minute).zfill(2)

            if use_unicode:
                time_str = f"{self._to_nepali_number(hours)}:{self._to_nepali_number(minutes)}"
            else:
                time_str = f"{hours}:{minutes}"

            return f"{date_str} {time_str}"

        except Exception as e:
            return ''
