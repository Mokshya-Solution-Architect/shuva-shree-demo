/** @odoo-module **/

import { DateTimePicker } from "@web/core/datetime/datetime_picker";
import { patch } from "@web/core/utils/patch";
import { useState, onWillStart } from "@odoo/owl";
import { nepaliDateConverter } from "./nepali_date_converter";
import { browser } from "@web/core/browser/browser";
import { deserializeDate, deserializeDateTime } from "@web/core/l10n/dates";

patch(DateTimePicker.prototype, {
    setup() {
        super.setup();

        // Initialize nepaliState immediately with default values
        this.nepaliState = useState({
            isBsMode: false,
            bsYear: null,
            bsMonth: null,
            bsDay: null,
            calendarDays: [],
            useUnicode: false, // Toggle for Nepali numerals and month names
            dateFormat: 'YYYY-MM-DD', // Default format
        });

        // Load saved preferences after initialization
        const savedMode = browser.localStorage.getItem('nepali_calendar_mode');
        if (savedMode === 'bs') {
            this.nepaliState.isBsMode = true;
        }

        const savedUnicode = browser.localStorage.getItem('nepali_unicode_mode');
        if (savedUnicode === 'true') {
            this.nepaliState.useUnicode = true;
        }

        const savedFormat = browser.localStorage.getItem('nepali_date_format');
        if (savedFormat) {
            this.nepaliState.dateFormat = savedFormat;
        }

        onWillStart(() => {
            if (this.nepaliState.isBsMode) {
                this.updateNepaliCalendar();
            }
        });
    },

    /**
     * Get year options for the dropdown (2000-2100)
     */
    getYearOptions() {
        const years = [];
        for (let year = 2000; year <= 2100; year++) {
            years.push(year);
        }
        return years;
    },

    /**
     * Get month options for the dropdown
     */
    getMonthOptions() {
        const months = [];
        for (let month = 1; month <= 12; month++) {
            const label = this.nepaliState.useUnicode
                ? nepaliDateConverter.getMonthName(month)
                : nepaliDateConverter.getMonthNameEnglish(month);
            months.push({ value: month, label: label });
        }
        return months;
    },

    /**
     * Handle month selection change
     */
    onBsMonthChange(event) {
        const newMonth = parseInt(event.target.value, 10);
        if (newMonth >= 1 && newMonth <= 12) {
            this.nepaliState.bsMonth = newMonth;
            this.updateCalendarAfterChange();
        }
    },

    /**
     * Handle year selection change
     */
    onBsYearChange(event) {
        const newYear = parseInt(event.target.value, 10);
        if (newYear >= 2000 && newYear <= 2100) {
            this.nepaliState.bsYear = newYear;
            this.updateCalendarAfterChange();
        }
    },

    /**
     * Update calendar after year/month change from dropdown
     */
    updateCalendarAfterChange() {
        // Ensure the day is valid for the new month/year
        const maxDays = nepaliDateConverter.getDaysInMonth(this.nepaliState.bsYear, this.nepaliState.bsMonth);
        if (this.nepaliState.bsDay > maxDays) {
            this.nepaliState.bsDay = maxDays;
        }

        // Update the focused date
        const adDate = nepaliDateConverter.bsToAd(
            this.nepaliState.bsYear,
            this.nepaliState.bsMonth,
            this.nepaliState.bsDay || 1
        );

        if (adDate && this.state && this.state.focusedDate !== undefined) {
            const dateStr = adDate.toISOString().split('T')[0];
            this.state.focusedDate = this.props.type === 'date'
                ? deserializeDate(dateStr)
                : deserializeDateTime(dateStr);
        }

        // Regenerate the calendar
        this.generateBsCalendar();
    },

    /**
     * Helper method to convert to Nepali number (accessible in template)
     */
    toNepaliNumber(num) {
        return nepaliDateConverter.toNepaliNumber(num);
    },

    /**
     * Toggle between AD and BS calendar
     */
    toggleCalendar() {
        this.nepaliState.isBsMode = !this.nepaliState.isBsMode;
        browser.localStorage.setItem('nepali_calendar_mode', this.nepaliState.isBsMode ? 'bs' : 'ad');

        // Update the calendar view with current date
        if (this.nepaliState.isBsMode) {
            // Switching to BS mode - convert current AD date to BS
            this.updateNepaliCalendar();
        }
        // When switching back to AD, the default calendar will show automatically
    },

    /**
     * Toggle Unicode mode (Nepali numerals and month names)
     */
    toggleUnicode() {
        this.nepaliState.useUnicode = !this.nepaliState.useUnicode;
        browser.localStorage.setItem('nepali_unicode_mode', this.nepaliState.useUnicode.toString());

        // Regenerate calendar with new format
        if (this.nepaliState.isBsMode) {
            this.generateBsCalendar();
        }
    },

    /**
     * Set date format
     */
    setDateFormat(format) {
        this.nepaliState.dateFormat = format;
        browser.localStorage.setItem('nepali_date_format', format);

        // Regenerate calendar with new format
        if (this.nepaliState.isBsMode) {
            this.generateBsCalendar();
        }
    },

    /**
     * Update Nepali calendar based on current date
     */
    updateNepaliCalendar() {
        if (!this.nepaliState.isBsMode) {
            return;
        }

        // Use the currently selected date from the picker's state, or today's date
        let currentDate = this.getSelectedDate();

        // Ensure currentDate is a valid Date object
        if (!(currentDate instanceof Date) || isNaN(currentDate.getTime())) {
            currentDate = new Date();
        }

        const bsDate = nepaliDateConverter.adToBs(currentDate);

        if (bsDate) {
            this.nepaliState.bsYear = bsDate.year;
            this.nepaliState.bsMonth = bsDate.month;
            this.nepaliState.bsDay = bsDate.day;
            this.generateBsCalendar();
        }
    },

    /**
     * Generate BS calendar days
     */
    generateBsCalendar() {
        // Validate BS year and month
        if (!this.nepaliState.bsYear || !this.nepaliState.bsMonth) {
            console.warn('Invalid BS year or month');
            return;
        }

        const daysInMonth = nepaliDateConverter.getDaysInMonth(
            this.nepaliState.bsYear,
            this.nepaliState.bsMonth
        );

        // Get the first day of the month in AD
        const firstDayAd = nepaliDateConverter.bsToAd(
            this.nepaliState.bsYear,
            this.nepaliState.bsMonth,
            1
        );

        // Check if conversion was successful
        if (!firstDayAd) {
            console.warn(`Cannot convert BS date ${this.nepaliState.bsYear}/${this.nepaliState.bsMonth}/1 to AD`);
            return;
        }

        const startDayOfWeek = firstDayAd.getDay(); // 0 = Sunday

        const calendarDays = [];

        // Get the currently selected date
        const selectedDate = this.getSelectedDate();

        // Add empty cells for days before the first day
        for (let i = 0; i < startDayOfWeek; i++) {
            calendarDays.push({ day: null, displayDay: '', isCurrentMonth: false });
        }

        // Add days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            let adDate = nepaliDateConverter.bsToAd(
                this.nepaliState.bsYear,
                this.nepaliState.bsMonth,
                day
            );

            // Skip if conversion failed
            if (!adDate) continue;

            // Normalize to midnight for date fields to avoid timezone issues
            if (this.props.type === 'date') {
                adDate = new Date(adDate.getFullYear(), adDate.getMonth(), adDate.getDate(), 0, 0, 0, 0);
            }

            const isToday = this.isToday(adDate);
            const isSelected = this.isSameDay(adDate, selectedDate);

            // Format day display based on Unicode preference
            const displayDay = this.nepaliState.useUnicode
                ? nepaliDateConverter.toNepaliNumber(day)
                : day;

            calendarDays.push({
                day: day,
                displayDay: displayDay,
                adDate: adDate,
                isCurrentMonth: true,
                isToday: isToday,
                isSelected: isSelected,
            });
        }

        this.nepaliState.calendarDays = calendarDays;
    },

    /**
     * Check if date is today
     */
    isToday(date) {
        if (!date) return false;
        const dateObj = date instanceof Date ? date : new Date(date);
        const today = new Date();
        return dateObj.getDate() === today.getDate() &&
               dateObj.getMonth() === today.getMonth() &&
               dateObj.getFullYear() === today.getFullYear();
    },

    /**
     * Check if two dates are the same day
     */
    isSameDay(date1, date2) {
        if (!date1 || !date2) return false;
        const d1 = date1 instanceof Date ? date1 : new Date(date1);
        const d2 = date2 instanceof Date ? date2 : new Date(date2);
        return d1.getDate() === d2.getDate() &&
               d1.getMonth() === d2.getMonth() &&
               d1.getFullYear() === d2.getFullYear();
    },

    /**
     * Get the currently selected date from picker state
     */
    getSelectedDate() {
        let date = this.state?.focusedDate ||
                   this.props.value ||
                   (this.props.range && this.props.range[0]);

        // If no date found, use today
        if (!date) {
            return new Date();
        }

        // Ensure we return a Date object
        if (date instanceof Date) {
            return date;
        }

        // If it's a luxon DateTime object
        if (date && typeof date === 'object' && date.toJSDate) {
            return date.toJSDate();
        }

        // If it's a string or timestamp
        return new Date(date);
    },

    /**
     * Handle BS date selection
     */
    onBsDayClick(dayInfo) {
        if (!dayInfo.isCurrentMonth || !dayInfo.adDate) return;

        // Format date string
        const year = dayInfo.adDate.getFullYear();
        const month = String(dayInfo.adDate.getMonth() + 1).padStart(2, '0');
        const day = String(dayInfo.adDate.getDate()).padStart(2, '0');
        const dateStr = `${year}-${month}-${day}`;

        // Use appropriate deserializer based on field type
        // For date fields, use deserializeDate to avoid timezone issues
        const luxonDate = this.props.type === 'date'
            ? deserializeDate(dateStr)
            : deserializeDateTime(dateStr);

        // Update the picker's internal state with the selected date
        if (this.state && this.state.focusedDate !== undefined) {
            this.state.focusedDate = luxonDate;
        }

        // Update nepali state - use the actual clicked day, not adDate's day
        this.nepaliState.bsDay = dayInfo.day;

        // Call the picker's select method with Luxon DateTime
        // onSelect expects (value, unit) where value is DateTime or [DateTime, DateTime] for ranges
        if (this.props.onSelect) {
            if (this.props.range) {
                this.props.onSelect([luxonDate, luxonDate], "date");
            } else {
                this.props.onSelect(luxonDate, "date");
            }
        }

        // Regenerate calendar to update selected state
        this.generateBsCalendar();
    },

    /**
     * Navigate to previous BS month
     */
    bsPrevMonth() {
        if (this.nepaliState.bsMonth === 1) {
            this.nepaliState.bsMonth = 12;
            this.nepaliState.bsYear--;
        } else {
            this.nepaliState.bsMonth--;
        }

        // Check if the new date is within valid range
        if (this.nepaliState.bsYear < 2000) {
            this.nepaliState.bsYear = 2000;
            this.nepaliState.bsMonth = 1;
        }

        // Update the state's focused date
        const day = Math.min(this.nepaliState.bsDay || 1, nepaliDateConverter.getDaysInMonth(this.nepaliState.bsYear, this.nepaliState.bsMonth));
        const adDate = nepaliDateConverter.bsToAd(
            this.nepaliState.bsYear,
            this.nepaliState.bsMonth,
            day
        );

        if (adDate && this.state && this.state.focusedDate !== undefined) {
            const dateStr = adDate.toISOString().split('T')[0];
            this.state.focusedDate = this.props.type === 'date'
                ? deserializeDate(dateStr)
                : deserializeDateTime(dateStr);
        }

        this.generateBsCalendar();
    },

    /**
     * Navigate to next BS month
     */
    bsNextMonth() {
        if (this.nepaliState.bsMonth === 12) {
            this.nepaliState.bsMonth = 1;
            this.nepaliState.bsYear++;
        } else {
            this.nepaliState.bsMonth++;
        }

        // Check if the new date is within valid range
        if (this.nepaliState.bsYear > 2100) {
            this.nepaliState.bsYear = 2100;
            this.nepaliState.bsMonth = 12;
        }

        // Update the state's focused date
        const day = Math.min(this.nepaliState.bsDay || 1, nepaliDateConverter.getDaysInMonth(this.nepaliState.bsYear, this.nepaliState.bsMonth));
        const adDate = nepaliDateConverter.bsToAd(
            this.nepaliState.bsYear,
            this.nepaliState.bsMonth,
            day
        );

        if (adDate && this.state && this.state.focusedDate !== undefined) {
            const dateStr = adDate.toISOString().split('T')[0];
            this.state.focusedDate = this.props.type === 'date'
                ? deserializeDate(dateStr)
                : deserializeDateTime(dateStr);
        }

        this.generateBsCalendar();
    },

    /**
     * Navigate to previous BS year
     */
    bsPrevYear() {
        this.nepaliState.bsYear--;

        // Check if the new year is within valid range
        if (this.nepaliState.bsYear < 2000) {
            this.nepaliState.bsYear = 2000;
        }

        const day = Math.min(this.nepaliState.bsDay || 1, nepaliDateConverter.getDaysInMonth(this.nepaliState.bsYear, this.nepaliState.bsMonth));
        const adDate = nepaliDateConverter.bsToAd(
            this.nepaliState.bsYear,
            this.nepaliState.bsMonth,
            day
        );

        if (adDate && this.state && this.state.focusedDate !== undefined) {
            const dateStr = adDate.toISOString().split('T')[0];
            this.state.focusedDate = this.props.type === 'date'
                ? deserializeDate(dateStr)
                : deserializeDateTime(dateStr);
        }

        this.generateBsCalendar();
    },

    /**
     * Navigate to next BS year
     */
    bsNextYear() {
        this.nepaliState.bsYear++;

        // Check if the new year is within valid range
        if (this.nepaliState.bsYear > 2100) {
            this.nepaliState.bsYear = 2100;
        }

        const day = Math.min(this.nepaliState.bsDay || 1, nepaliDateConverter.getDaysInMonth(this.nepaliState.bsYear, this.nepaliState.bsMonth));
        const adDate = nepaliDateConverter.bsToAd(
            this.nepaliState.bsYear,
            this.nepaliState.bsMonth,
            day
        );

        if (adDate && this.state && this.state.focusedDate !== undefined) {
            const dateStr = adDate.toISOString().split('T')[0];
            this.state.focusedDate = this.props.type === 'date'
                ? deserializeDate(dateStr)
                : deserializeDateTime(dateStr);
        }

        this.generateBsCalendar();
    },

    /**
     * Get formatted date for display
     */
    getFormattedDate() {
        const selectedDate = this.getSelectedDate();
        if (!selectedDate) return '';

        // Ensure we have a Date object
        const dateObj = selectedDate instanceof Date ? selectedDate : new Date(selectedDate);

        if (this.nepaliState.isBsMode) {
            const bsDate = nepaliDateConverter.adToBs(dateObj);
            if (bsDate) {
                return nepaliDateConverter.formatBsDate(
                    bsDate,
                    this.nepaliState.dateFormat,
                    this.nepaliState.useUnicode
                );
            }
        }

        return dateObj.toLocaleDateString();
    },

    /**
     * Get month name for display
     */
    getMonthName() {
        if (this.nepaliState.isBsMode && this.nepaliState.bsMonth) {
            return this.nepaliState.useUnicode
                ? nepaliDateConverter.getMonthName(this.nepaliState.bsMonth)
                : nepaliDateConverter.getMonthNameEnglish(this.nepaliState.bsMonth);
        }
        const date = this.getSelectedDate();
        return date ? new Date(date).toLocaleDateString('default', { month: 'long' }) : '';
    },

    /**
     * Get year for display
     */
    getYear() {
        if (this.nepaliState.isBsMode && this.nepaliState.bsYear) {
            return this.nepaliState.useUnicode
                ? nepaliDateConverter.toNepaliNumber(this.nepaliState.bsYear)
                : this.nepaliState.bsYear;
        }
        const date = this.getSelectedDate();
        return date ? new Date(date).getFullYear() : new Date().getFullYear();
    },

    /**
     * Get weekday names for calendar header
     */
    getWeekdayNames() {
        const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const nepaliWeekdays = ['आइत', 'सोम', 'मंगल', 'बुध', 'बिहि', 'शुक्र', 'शनि'];

        if (this.nepaliState.isBsMode && this.nepaliState.useUnicode) {
            return nepaliWeekdays;
        }
        return weekdays;
    },
});