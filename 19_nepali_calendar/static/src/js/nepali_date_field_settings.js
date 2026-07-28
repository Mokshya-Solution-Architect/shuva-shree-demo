/** @odoo-module **/

import { DateTimeField } from "@web/views/fields/datetime/datetime_field";
import { patch } from "@web/core/utils/patch";
import { useState, onWillStart } from "@odoo/owl";
import { nepaliDateConverter } from "./nepali_date_converter";
import { useService } from "@web/core/utils/hooks";

patch(DateTimeField.prototype, {
    setup() {
        super.setup();

        // Get nepali calendar service
        this.nepaliCalendarService = useService("nepali_calendar");

        // Initialize nepali field state
        this.nepaliFieldState = useState({
            isBsMode: false,
            useUnicode: false,
            dateFormat: 'YYYY-MM-DD',
            settings: null,
        });

        // Load settings from backend
        onWillStart(async () => {
            try {
                const settings = await this.nepaliCalendarService.getSettings();
                this.nepaliFieldState.settings = settings;

                // Apply settings
                if (settings.enable) {
                    // Determine format based on field type
                    const isDateField = this.field.type === 'date';
                    const formatSetting = isDateField ? settings.date_format : settings.datetime_format;

                    // Set Unicode mode
                    this.nepaliFieldState.useUnicode =
                        settings.date_format === 'bs_unicode' ||
                        settings.datetime_format === 'bs_unicode';

                    // Set date pattern
                    this.nepaliFieldState.dateFormat = settings.date_pattern || 'YYYY-MM-DD';

                    console.log('[Nepali DateField] Configuration:', {
                        fieldType: this.field.type,
                        fieldName: this.props.name,
                        formatSetting,
                        useUnicode: this.nepaliFieldState.useUnicode,
                        datePattern: this.nepaliFieldState.dateFormat
                    });
                }
            } catch (error) {
                console.error('[Nepali DateField] Failed to load settings:', error);
            }
        });
    },

    /**
     * Toggle Nepali mode for the calendar (only if calendar_mode is 'both')
     */
    toggleNepaliMode() {
        if (this.nepaliFieldState.settings &&
            this.nepaliFieldState.settings.calendar_mode === 'both') {
            this.nepaliFieldState.isBsMode = !this.nepaliFieldState.isBsMode;
        }
    },

    /**
     * Get formatted value for display with conditional formatting based on settings
     * This method is called for ALL views: form, list, kanban, calendar, etc.
     */
    getFormattedValue(valueIndex, numeric) {
        const value = this.values[valueIndex];

        if (!value) {
            return '';
        }

        try {
            const settings = this.nepaliFieldState.settings;

            // If Nepali calendar is not enabled, use default formatting
            if (!settings || !settings.enable) {
                return super.getFormattedValue(valueIndex, numeric);
            }

            // Convert Luxon DateTime to JS Date
            let jsDate = value.toJSDate ? value.toJSDate() : new Date(value);

            // Normalize to local midnight for date fields to avoid timezone issues
            if (this.field.type === 'date') {
                jsDate = new Date(jsDate.getFullYear(), jsDate.getMonth(), jsDate.getDate(), 0, 0, 0, 0);
            }

            const isDateField = this.field.type === 'date';
            const formatSetting = isDateField ? settings.date_format : settings.datetime_format;

            // Handle different format settings
            if (formatSetting === 'ad_only') {
                return super.getFormattedValue(valueIndex, numeric);
            }

            // Convert to BS
            const bsDate = nepaliDateConverter.adToBs(jsDate);
            if (!bsDate) {
                return super.getFormattedValue(valueIndex, numeric);
            }

            const useUnicode = formatSetting === 'bs_unicode';
            const pattern = settings.date_pattern || 'YYYY-MM-DD';

            // Get formatted BS date
            let bsFormatted;
            if (isDateField) {
                bsFormatted = this.formatBsDate(bsDate, jsDate, pattern, useUnicode);
            } else {
                bsFormatted = this.formatBsDateTime(bsDate, jsDate, pattern, useUnicode);
            }

            // Handle combined format (BS + AD)
            if (formatSetting === 'bs_ad_combined') {
                const adFormatted = super.getFormattedValue(valueIndex, numeric);
                return `${bsFormatted} (${adFormatted})`;
            }

            return bsFormatted;

        } catch (error) {
            console.warn('Error formatting date:', error);
            return super.getFormattedValue(valueIndex, numeric);
        }
    },

    /**
     * Format BS date
     */
    formatBsDate(bsDate, jsDate, pattern, useUnicode) {
        const monthName = useUnicode
            ? nepaliDateConverter.getMonthName(bsDate.month)
            : nepaliDateConverter.getMonthNameEnglish(bsDate.month);

        if (pattern === 'YYYY MMMM DD') {
            const year = useUnicode ? nepaliDateConverter.toNepaliNumber(bsDate.year) : bsDate.year;
            const day = useUnicode ? nepaliDateConverter.toNepaliNumber(bsDate.day) : bsDate.day;
            return `${year} ${monthName} ${day}`;
        } else if (pattern === 'DD MMMM YYYY') {
            const year = useUnicode ? nepaliDateConverter.toNepaliNumber(bsDate.year) : bsDate.year;
            const day = useUnicode ? nepaliDateConverter.toNepaliNumber(bsDate.day) : bsDate.day;
            return `${day} ${monthName} ${year}`;
        } else { // YYYY-MM-DD
            const year = useUnicode ? nepaliDateConverter.toNepaliNumber(bsDate.year) : bsDate.year;
            const month = String(bsDate.month).padStart(2, '0');
            const day = String(bsDate.day).padStart(2, '0');
            const monthStr = useUnicode ? nepaliDateConverter.toNepaliNumber(month) : month;
            const dayStr = useUnicode ? nepaliDateConverter.toNepaliNumber(day) : day;
            return `${year}-${monthStr}-${dayStr}`;
        }
    },

    /**
     * Format BS datetime
     */
    formatBsDateTime(bsDate, jsDate, pattern, useUnicode) {
        const datePart = this.formatBsDate(bsDate, jsDate, pattern, useUnicode);

        // Get time part
        const hours = String(jsDate.getHours()).padStart(2, '0');
        const minutes = String(jsDate.getMinutes()).padStart(2, '0');

        const timeStr = useUnicode
            ? `${nepaliDateConverter.toNepaliNumber(hours)}:${nepaliDateConverter.toNepaliNumber(minutes)}`
            : `${hours}:${minutes}`;

        return `${datePart} ${timeStr}`;
    },
});
