/** @odoo-module **/

/**
 * Nepali Date Converter
 * Converts between Gregorian (A.D.) and Bikram Sambat (B.S.) calendars
 */

export class NepaliDateConverter {
    constructor() {
        // Nepali calendar data - days in each month for different years
        // Format: [year] = [days_in_months]
        this.calendarData = this.getCalendarData();
        this.minBsYear = 2000;
        this.maxBsYear = 2100;
        // Reference date verified:
        // BS 2000/01/01 = AD 1943/04/14
        // Verified using: Nov 28, 2025 = Mangsir 12, 2082
        this.minAdDate = new Date(1943, 3, 14); // 2000/01/01 BS = April 14, 1943
        this.maxAdDate = new Date(2043, 3, 12); // 2099/12/30 BS
    }

    /**
     * Calendar data for Nepali calendar (Bikram Sambat)
     * Source: Official Nepali Functions JavaScript Library
     * Each array represents days in 12 months (Baisakh to Chaitra) for that year
     * Format: [Baisakh, Jestha, Ashar, Shrawan, Bhadra, Ashoj, Kartik, Mangsir, Poush, Magh, Falgun, Chaitra]
     */
    getCalendarData() {
        return {
            // BS 2000-2009
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

            // BS 2010-2019
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

            // BS 2020-2029
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

            // BS 2030-2039
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

            // BS 2040-2049
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

            // BS 2050-2059
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

            // BS 2060-2069
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

            // BS 2070-2079
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

            // BS 2080-2089
            2080: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
            2081: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
            2082: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
            2083: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
            2084: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
            2085: [31, 32, 31, 32, 30, 31, 30, 30, 29, 30, 30, 30],
            2086: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
            2087: [31, 31, 32, 31, 31, 31, 30, 30, 29, 30, 30, 30],
            2088: [30, 31, 32, 32, 30, 31, 30, 30, 29, 30, 30, 30],
            2089: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],

            // BS 2090-2099
            2090: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
            2091: [31, 31, 32, 31, 31, 31, 30, 30, 29, 30, 30, 30],
            2092: [30, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
            2093: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
            2094: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
            2095: [31, 31, 32, 31, 31, 31, 30, 29, 30, 30, 30, 30],
            2096: [30, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
            2097: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
            2098: [31, 31, 32, 31, 31, 31, 29, 30, 29, 30, 29, 31],
            2099: [31, 31, 32, 31, 31, 31, 30, 29, 29, 30, 30, 30],

            // BS 2100 (partial support)
            2100: [31, 32, 31, 32, 30, 31, 30, 29, 30, 29, 30, 30],
        };
    }

    /**
     * Convert date to Nepal timezone (GMT+5:45)
     * @param {Date} date - Date in any timezone
     * @returns {Date} - Date adjusted to Nepal timezone
     */
    toNepalTime(date) {
        // Get the date in Nepal timezone using toLocaleString
        const nepaliTimeStr = date.toLocaleString('en-US', {
            timeZone: 'Asia/Kathmandu',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });

        // Parse the Nepal time string (format: MM/DD/YYYY, HH:mm:ss)
        const [datePart] = nepaliTimeStr.split(', ');
        const [month, day, year] = datePart.split('/').map(Number);

        // Return a new Date object representing the Nepal date
        // Note: We create this in UTC to avoid timezone conversion
        return new Date(Date.UTC(year, month - 1, day, 0, 0, 0, 0));
    }

    /**
     * Convert Gregorian date to Nepali date
     * @param {Date} adDate - Gregorian date
     * @returns {Object} - {year, month, day, dayOfWeek}
     */
    adToBs(adDate) {
        if (!(adDate instanceof Date) || isNaN(adDate)) {
            return null;
        }

        // Convert to Nepal timezone first
        const nepalDate = this.toNepalTime(adDate);

        // Normalize both dates to midnight UTC to avoid timezone issues
        const normalizedAdDate = new Date(Date.UTC(
            nepalDate.getUTCFullYear(),
            nepalDate.getUTCMonth(),
            nepalDate.getUTCDate(),
            0, 0, 0, 0
        ));
        const normalizedMinDate = new Date(Date.UTC(
            this.minAdDate.getFullYear(),
            this.minAdDate.getMonth(),
            this.minAdDate.getDate(),
            0, 0, 0, 0
        ));

        // Calculate days difference from reference date
        const diffTime = normalizedAdDate - normalizedMinDate;
        let totalDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

        let bsYear = this.minBsYear;
        let bsMonth = 1;
        let bsDay = 1;

        // Calculate year
        while (bsYear <= this.maxBsYear) {
            const daysInYear = this.getDaysInYear(bsYear);
            if (totalDays < daysInYear) {
                break;
            }
            totalDays -= daysInYear;
            bsYear++;
        }

        // Calculate month
        for (let month = 1; month <= 12; month++) {
            const daysInMonth = this.getDaysInMonth(bsYear, month);
            if (totalDays < daysInMonth) {
                bsMonth = month;
                bsDay = totalDays + 1;
                break;
            }
            totalDays -= daysInMonth;
        }

        // Calculate day of week for the Nepal date
        const nepaliDayOfWeek = new Date(nepalDate.getUTCFullYear(), nepalDate.getUTCMonth(), nepalDate.getUTCDate()).getDay();

        return {
            year: bsYear,
            month: bsMonth,
            day: bsDay,
            dayOfWeek: nepaliDayOfWeek,
        };
    }

    /**
     * Convert Nepali date to Gregorian date
     * @param {number} bsYear
     * @param {number} bsMonth
     * @param {number} bsDay
     * @returns {Date} - Gregorian date
     */
    bsToAd(bsYear, bsMonth, bsDay) {
        if (bsYear < this.minBsYear || bsYear > this.maxBsYear) {
            return null;
        }

        let totalDays = 0;

        // Add days for complete years
        for (let year = this.minBsYear; year < bsYear; year++) {
            totalDays += this.getDaysInYear(year);
        }

        // Add days for complete months
        for (let month = 1; month < bsMonth; month++) {
            totalDays += this.getDaysInMonth(bsYear, month);
        }

        // Add remaining days
        totalDays += bsDay - 1;

        // Calculate AD date using milliseconds to avoid timezone issues
        const baseTime = this.minAdDate.getTime();
        const millisecondsToAdd = totalDays * 24 * 60 * 60 * 1000;
        const adDate = new Date(baseTime + millisecondsToAdd);

        // Normalize to local midnight to avoid timezone issues
        return new Date(adDate.getFullYear(), adDate.getMonth(), adDate.getDate(), 0, 0, 0, 0);
    }

    /**
     * Get total days in a BS year
     * @param {number} year
     * @returns {number}
     */
    getDaysInYear(year) {
        if (!this.calendarData[year]) {
            return 365;
        }
        return this.calendarData[year].reduce((sum, days) => sum + days, 0);
    }

    /**
     * Get days in a specific BS month
     * @param {number} year
     * @param {number} month (1-12)
     * @returns {number}
     */
    getDaysInMonth(year, month) {
        if (!this.calendarData[year]) {
            return 30;
        }
        return this.calendarData[year][month - 1];
    }

    /**
     * Get Nepali month name
     * @param {number} month (1-12)
     * @returns {string}
     */
    getMonthName(month) {
        const months = [
            'बैशाख', 'जेठ', 'असार', 'साउन',
            'भदौ', 'असोज', 'कार्तिक', 'मंसिर',
            'पुष', 'माघ', 'फागुन', 'चैत'
        ];
        return months[month - 1];
    }

    /**
     * Get Nepali month name in English
     * @param {number} month (1-12)
     * @returns {string}
     */
    getMonthNameEnglish(month) {
        const months = [
            'Baisakh', 'Jestha', 'Ashar', 'Shrawan',
            'Bhadra', 'Ashoj', 'Kartik', 'Mangsir',
            'Poush', 'Magh', 'Falgun', 'Chaitra'
        ];
        return months[month - 1];
    }

    /**
     * Convert English numbers to Nepali numerals
     * @param {number|string} num
     * @returns {string}
     */
    toNepaliNumber(num) {
        const nepaliNumerals = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'];
        return String(num).split('').map(digit => nepaliNumerals[digit] || digit).join('');
    }

    /**
     * Convert Nepali numerals to English numbers
     * @param {string} nepaliNum
     * @returns {number}
     */
    toEnglishNumber(nepaliNum) {
        const nepaliToEnglish = {
            '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
            '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
        };
        const englishStr = String(nepaliNum).split('').map(char => nepaliToEnglish[char] || char).join('');
        return Number(englishStr);
    }

    /**
     * Get Nepali day name
     * @param {number} dayIndex (0-6, where 0 is Sunday)
     * @returns {string}
     */
    getDayName(dayIndex) {
        const days = ['आइतबार', 'सोमबार', 'मंगलबार', 'बुधबार', 'बिहिबार', 'शुक्रबार', 'शनिबार'];
        return days[dayIndex];
    }

    /**
     * Get English day name
     * @param {number} dayIndex (0-6, where 0 is Sunday)
     * @returns {string}
     */
    getDayNameEnglish(dayIndex) {
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        return days[dayIndex];
    }

    /**
     * Get short Nepali day name
     * @param {number} dayIndex (0-6)
     * @returns {string}
     */
    getDayNameShort(dayIndex) {
        const days = ['आइत', 'सोम', 'मंगल', 'बुध', 'बिहि', 'शुक्र', 'शनि'];
        return days[dayIndex];
    }

    /**
     * Get short English day name
     * @param {number} dayIndex (0-6)
     * @returns {string}
     */
    getDayNameShortEnglish(dayIndex) {
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        return days[dayIndex];
    }

    /**
     * Parse date string in various formats
     * @param {string} dateStr - Date string in formats: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY
     * @param {string} format - Expected format (optional)
     * @returns {Object} - {year, month, day} or null
     */
    parseDate(dateStr, format = 'YYYY-MM-DD') {
        if (!dateStr) return null;

        // Convert Nepali numerals to English if present
        dateStr = dateStr.split('').map(char => {
            const nepaliToEnglish = {
                '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
                '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
            };
            return nepaliToEnglish[char] || char;
        }).join('');

        let parts;
        if (dateStr.includes('-')) {
            parts = dateStr.split('-');
        } else if (dateStr.includes('/')) {
            parts = dateStr.split('/');
        } else {
            return null;
        }

        if (parts.length !== 3) return null;

        let year, month, day;

        switch (format) {
            case 'YYYY-MM-DD':
            case 'YYYY/MM/DD':
                [year, month, day] = parts.map(Number);
                break;
            case 'DD-MM-YYYY':
            case 'DD/MM/YYYY':
                [day, month, year] = parts.map(Number);
                break;
            case 'MM-DD-YYYY':
            case 'MM/DD/YYYY':
                [month, day, year] = parts.map(Number);
                break;
            default:
                return null;
        }

        return { year, month, day };
    }

    /**
     * Format BS date as string with various format options
     * @param {Object} bsDate - {year, month, day}
     * @param {string} format - Format string (YYYY-MM-DD, DD/MM/YYYY, etc.)
     * @param {boolean} useUnicode - Use Nepali numerals and month names
     * @returns {string}
     */
    formatBsDate(bsDate, format = 'YYYY-MM-DD', useUnicode = false) {
        if (!bsDate) return '';

        const year = String(bsDate.year).padStart(4, '0');
        const month = String(bsDate.month).padStart(2, '0');
        const day = String(bsDate.day).padStart(2, '0');

        let formatted = '';

        switch (format) {
            case 'YYYY-MM-DD':
                formatted = `${year}-${month}-${day}`;
                break;
            case 'YYYY/MM/DD':
                formatted = `${year}/${month}/${day}`;
                break;
            case 'DD-MM-YYYY':
                formatted = `${day}-${month}-${year}`;
                break;
            case 'DD/MM/YYYY':
                formatted = `${day}/${month}/${year}`;
                break;
            case 'MMMM DD, YYYY':
                if (useUnicode) {
                    formatted = `${this.getMonthName(bsDate.month)} ${this.toNepaliNumber(day)}, ${this.toNepaliNumber(year)}`;
                } else {
                    formatted = `${this.getMonthNameEnglish(bsDate.month)} ${day}, ${year}`;
                }
                break;
            case 'DD MMMM YYYY':
                if (useUnicode) {
                    formatted = `${this.toNepaliNumber(day)} ${this.getMonthName(bsDate.month)} ${this.toNepaliNumber(year)}`;
                } else {
                    formatted = `${day} ${this.getMonthNameEnglish(bsDate.month)} ${year}`;
                }
                break;
            case 'MMMM YYYY':
                if (useUnicode) {
                    formatted = `${this.getMonthName(bsDate.month)} ${this.toNepaliNumber(year)}`;
                } else {
                    formatted = `${this.getMonthNameEnglish(bsDate.month)} ${year}`;
                }
                break;
            default:
                formatted = `${year}-${month}-${day}`;
        }

        if (useUnicode && /^\d/.test(formatted)) {
            // Convert numbers to Nepali if format starts with digits
            formatted = formatted.split('').map(char => {
                if (/\d/.test(char)) {
                    return this.toNepaliNumber(char);
                }
                return char;
            }).join('');
        }

        return formatted;
    }

    /**
     * Get full formatted date with day name
     * @param {Object} bsDate - {year, month, day, dayOfWeek}
     * @param {boolean} useUnicode - Use Nepali characters
     * @returns {string}
     */
    getFullDate(bsDate, useUnicode = false) {
        if (!bsDate) return '';

        const dayOfWeek = bsDate.dayOfWeek !== undefined ? bsDate.dayOfWeek :
            this.bsToAd(bsDate.year, bsDate.month, bsDate.day)?.getDay() || 0;

        if (useUnicode) {
            return `${this.getDayName(dayOfWeek)}, ${this.toNepaliNumber(bsDate.day)} ${this.getMonthName(bsDate.month)} ${this.toNepaliNumber(bsDate.year)}`;
        } else {
            return `${this.getDayNameEnglish(dayOfWeek)}, ${bsDate.day} ${this.getMonthNameEnglish(bsDate.month)} ${bsDate.year}`;
        }
    }

    /**
     * Add days to a BS date
     * @param {Object} bsDate - {year, month, day}
     * @param {number} days - Number of days to add (can be negative)
     * @returns {Object} - New BS date
     */
    addDays(bsDate, days) {
        if (!bsDate) return null;

        // Convert to AD, add days, convert back to BS
        const adDate = this.bsToAd(bsDate.year, bsDate.month, bsDate.day);
        if (!adDate) return null;

        adDate.setDate(adDate.getDate() + days);
        return this.adToBs(adDate);
    }

    /**
     * Calculate difference between two BS dates in days
     * @param {Object} bsDate1 - {year, month, day}
     * @param {Object} bsDate2 - {year, month, day}
     * @returns {number} - Difference in days
     */
    dateDiff(bsDate1, bsDate2) {
        if (!bsDate1 || !bsDate2) return null;

        const ad1 = this.bsToAd(bsDate1.year, bsDate1.month, bsDate1.day);
        const ad2 = this.bsToAd(bsDate2.year, bsDate2.month, bsDate2.day);

        if (!ad1 || !ad2) return null;

        const diffTime = ad2.getTime() - ad1.getTime();
        return Math.round(diffTime / (1000 * 60 * 60 * 24));
    }

    /**
     * Compare two BS dates
     * @param {Object} bsDate1 - {year, month, day}
     * @param {Object} bsDate2 - {year, month, day}
     * @returns {number} - -1 if date1 < date2, 0 if equal, 1 if date1 > date2
     */
    compareDates(bsDate1, bsDate2) {
        if (!bsDate1 || !bsDate2) return null;

        const val1 = bsDate1.year * 10000 + bsDate1.month * 100 + bsDate1.day;
        const val2 = bsDate2.year * 10000 + bsDate2.month * 100 + bsDate2.day;

        if (val1 < val2) return -1;
        if (val1 > val2) return 1;
        return 0;
    }

    /**
     * Check if BS date is valid
     * @param {number} year
     * @param {number} month
     * @param {number} day
     * @returns {boolean}
     */
    isValidDate(year, month, day) {
        if (year < this.minBsYear || year > this.maxBsYear) return false;
        if (month < 1 || month > 12) return false;

        const daysInMonth = this.getDaysInMonth(year, month);
        if (day < 1 || day > daysInMonth) return false;

        return true;
    }

    /**
     * Get current BS date (using Nepal timezone)
     * @returns {Object} - {year, month, day, dayOfWeek}
     */
    getCurrentBsDate() {
        // Create a new date representing "now" in Nepal timezone
        const now = new Date();
        return this.adToBs(now);
    }

    /**
     * Get current Nepal date and time
     * @returns {Date} - Current date in Nepal timezone
     */
    getCurrentNepalTime() {
        return this.toNepalTime(new Date());
    }

    /**
     * Get month name with zero-based index
     * @param {number} monthIndex (0-11)
     * @returns {string}
     */
    getMonthNameByIndex(monthIndex) {
        return this.getMonthName(monthIndex + 1);
    }

    /**
     * Get English month name with zero-based index
     * @param {number} monthIndex (0-11)
     * @returns {string}
     */
    getMonthNameEnglishByIndex(monthIndex) {
        return this.getMonthNameEnglish(monthIndex + 1);
    }
}

export const nepaliDateConverter = new NepaliDateConverter();