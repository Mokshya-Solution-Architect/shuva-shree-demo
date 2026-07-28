/** @odoo-module **/

import { DateTimeField } from "@web/views/fields/datetime/datetime_field";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { nepaliDateConverter } from "./nepali_date_converter";
import { browser } from "@web/core/browser/browser";

patch(DateTimeField.prototype, {
    setup() {
        super.setup();

        // Initialize nepali field state
        this.nepaliFieldState = useState({
            isBsMode: false,
            useUnicode: false,
        });

        // Load saved preferences
        const savedMode = browser.localStorage.getItem('nepali_calendar_mode');
        if (savedMode === 'bs') {
            this.nepaliFieldState.isBsMode = true;
        }

        const savedUnicode = browser.localStorage.getItem('nepali_unicode_mode');
        if (savedUnicode === 'true') {
            this.nepaliFieldState.useUnicode = true;
        }
    },

    /**
     * Toggle Nepali mode for the calendar
     */
    toggleNepaliMode() {
        this.nepaliFieldState.isBsMode = !this.nepaliFieldState.isBsMode;
        browser.localStorage.setItem('nepali_calendar_mode', this.nepaliFieldState.isBsMode ? 'bs' : 'ad');
    },

    /**
     * Get formatted value for display with conditional formatting
     */
    getFormattedValue(valueIndex, numeric) {
        const value = this.values[valueIndex];

        if (!value) {
            return '';
        }

        try {
            // Convert Luxon DateTime to JS Date
            let jsDate = value.toJSDate ? value.toJSDate() : new Date(value);

            // Normalize to local midnight for date fields to avoid timezone issues
            if (this.field.type === 'date') {
                jsDate = new Date(jsDate.getFullYear(), jsDate.getMonth(), jsDate.getDate(), 0, 0, 0, 0);
            }

            // Convert to BS
            const bsDate = nepaliDateConverter.adToBs(jsDate);

            if (!bsDate) {
                // If conversion fails, return original formatted value
                return super.getFormattedValue(valueIndex, numeric);
            }

            // Check if in BS mode
            if (this.nepaliFieldState.isBsMode) {
                // BS Mode: Show BS date in YYYY MMMM DD format with Unicode support
                const useUnicode = this.nepaliFieldState.useUnicode;

                // Get month name based on Unicode preference
                const monthName = useUnicode
                    ? nepaliDateConverter.getMonthName(bsDate.month)
                    : nepaliDateConverter.getMonthNameEnglish(bsDate.month);

                // Format year and day based on Unicode preference
                const year = useUnicode
                    ? nepaliDateConverter.toNepaliNumber(bsDate.year)
                    : bsDate.year;
                const day = useUnicode
                    ? nepaliDateConverter.toNepaliNumber(String(bsDate.day).padStart(2, '0'))
                    : String(bsDate.day).padStart(2, '0');

                if (this.field.type === 'datetime') {
                    // For datetime fields, include time
                    const hours = String(jsDate.getHours()).padStart(2, '0');
                    const minutes = String(jsDate.getMinutes()).padStart(2, '0');
                    const seconds = String(jsDate.getSeconds()).padStart(2, '0');

                    const timeStr = useUnicode
                        ? `${nepaliDateConverter.toNepaliNumber(hours)}:${nepaliDateConverter.toNepaliNumber(minutes)}`
                        : `${hours}:${minutes}`;

                    if (this.props.showSeconds) {
                        const secStr = useUnicode ? nepaliDateConverter.toNepaliNumber(seconds) : seconds;
                        return `${year} ${monthName} ${day} ${timeStr}:${secStr}`;
                    } else {
                        return `${year} ${monthName} ${day} ${timeStr}`;
                    }
                } else {
                    // For date fields: YYYY MMMM DD format
                    return `${year} ${monthName} ${day}`;
                }
            } else {
                // A.D. Mode: Show original AD date
                return super.getFormattedValue(valueIndex, numeric);
            }
        } catch (error) {
            console.warn('Error formatting date:', error);
            return super.getFormattedValue(valueIndex, numeric);
        }
    },
});
