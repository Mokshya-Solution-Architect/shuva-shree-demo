/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { DateTimeField } from "@web/views/fields/datetime/datetime_field";
import {
    formatDate as _formatDate,
    formatDateTime as _formatDateTime,
} from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { nepaliDateConverter } from "./nepali_date_converter";

// Global settings cache to avoid repeated async calls
let _cachedSettings = null;
let _settingsPromise = null;

/**
 * Load settings from backend (with caching) using RPC directly
 */
async function loadSettings() {
    if (_cachedSettings) {
        return _cachedSettings;
    }

    if (_settingsPromise) {
        return _settingsPromise;
    }

    _settingsPromise = rpc('/nepali_calendar/get_settings')
        .then((settings) => {
            _cachedSettings = settings;
            console.log('[Nepali Calendar Enhanced] Settings loaded from backend:', settings);
            return settings;
        })
        .catch((error) => {
            console.error('[Nepali Calendar Enhanced] Error loading settings:', error);
            _cachedSettings = {
                enable: false,
                date_format: 'ad_only',
                datetime_format: 'ad_only',
                date_pattern: 'YYYY MMMM DD',
                datetime_pattern: 'YYYY MMMM DD HH:mm',
                calendar_mode: 'ad'
            };
            return _cachedSettings;
        });

    return _settingsPromise;
}

/**
 * Get settings synchronously (returns cached settings or defaults)
 */
function getSettings() {
    if (_cachedSettings) {
        return _cachedSettings;
    }
    // Return defaults if not loaded yet
    return {
        enable: false,
        date_format: 'ad_only',
        datetime_format: 'ad_only',
        date_pattern: 'YYYY MMMM DD',
        datetime_pattern: 'YYYY MMMM DD HH:mm',
        calendar_mode: 'ad'
    };
}

/**
 * Check if BS date should be shown for date fields
 */
function shouldShowBsDate() {
    const settings = getSettings();
    const shouldShow = settings.enable && settings.date_format !== 'ad_only';
    console.log('[Nepali Calendar Enhanced] Should show BS (date):', shouldShow, '| Format:', settings.date_format);
    return shouldShow;
}

/**
 * Check if BS date should be shown for datetime fields
 */
function shouldShowBsDateTime() {
    const settings = getSettings();
    const shouldShow = settings.enable && settings.datetime_format !== 'ad_only';
    console.log('[Nepali Calendar Enhanced] Should show BS (datetime):', shouldShow, '| Format:', settings.datetime_format);
    return shouldShow;
}

/**
 * Check if Unicode should be used
 */
function shouldUseUnicode(isDateField = true) {
    const settings = getSettings();
    const format = isDateField ? settings.date_format : settings.datetime_format;
    return format === 'bs_unicode';
}

/**
 * Get date format pattern
 */
function getDateFormat(isDateField = true) {
    const settings = getSettings();
    return isDateField ? settings.date_pattern : settings.datetime_pattern;
}

/**
 * Check if combined format should be used
 */
function isCombinedFormat(isDateField = true) {
    const settings = getSettings();
    const format = isDateField ? settings.date_format : settings.datetime_format;
    return format === 'bs_ad_combined';
}

/**
 * Convert and format AD date to BS
 */
function formatBsDateFromAd(value, includeTime = false, options = {}) {
    try {
        const dateObj = new Date(value);
        const bsDate = nepaliDateConverter.adToBs(dateObj);

        if (!bsDate) {
            return "Date out of range";
        }

        const useUnicode = shouldUseUnicode(!includeTime);
        const format = getDateFormat(!includeTime);
        const formattedDate = nepaliDateConverter.formatBsDate(bsDate, format, useUnicode);

        if (includeTime && options.showTime !== false) {
            const hours = String(dateObj.getHours()).padStart(2, '0');
            const minutes = String(dateObj.getMinutes()).padStart(2, '0');
            const timeStr = useUnicode
                ? `${nepaliDateConverter.toNepaliNumber(hours)}:${nepaliDateConverter.toNepaliNumber(minutes)}`
                : `${hours}:${minutes}`;

            if (options.showSeconds) {
                const seconds = String(dateObj.getSeconds()).padStart(2, '0');
                const secStr = useUnicode ? nepaliDateConverter.toNepaliNumber(seconds) : seconds;
                return `${formattedDate} ${timeStr}:${secStr}`;
            }

            return `${formattedDate} ${timeStr}`;
        }

        return formattedDate;
    } catch (error) {
        console.error("Error converting to BS date:", error);
        return "Conversion error";
    }
}

/**
 * Custom DateTime formatter that shows BS dates based on user preference
 */
export function myformatDateTime(value, options = {}) {
    if (!value) return '';

    const settings = getSettings();
    const format = settings.datetime_format;

    // Handle combined format: "BS (AD)"
    if (format === 'bs_ad_combined' && settings.enable) {
        const bsFormatted = formatBsDateFromAd(value, true, options);
        const adFormatted = options.showTime === false
            ? _formatDate(value, options)
            : _formatDateTime(value, options);
        return `${bsFormatted} (${adFormatted})`;
    }

    // Handle BS only formats
    if (shouldShowBsDateTime()) {
        return formatBsDateFromAd(value, true, options);
    }

    // Default: AD format
    if (options.showTime === false) {
        return _formatDate(value, options);
    }
    return _formatDateTime(value, options);
}

/**
 * Custom Date formatter that shows BS dates based on user preference
 */
export function myformatDate(value, options = {}) {
    if (!value) return '';

    const settings = getSettings();
    const format = settings.date_format;

    // Handle combined format: "BS (AD)"
    if (format === 'bs_ad_combined' && settings.enable) {
        const bsFormatted = formatBsDateFromAd(value, false, options);
        const adFormatted = _formatDate(value, options);
        return `${bsFormatted} (${adFormatted})`;
    }

    // Handle BS only formats
    if (shouldShowBsDate()) {
        return formatBsDateFromAd(value, false, options);
    }

    // Default: AD format
    return _formatDate(value, options);
}

/**
 * Format date for list view with both AD and BS
 * Shows: "AD Date (BS Date)" format
 */
export function formatDateWithBs(value, options = {}) {
    if (!value) return '';

    const adFormatted = _formatDate(value, options);

    try {
        const dateObj = new Date(value);
        const bsDate = nepaliDateConverter.adToBs(dateObj);

        if (bsDate) {
            const useUnicode = shouldUseUnicode();
            const bsFormatted = nepaliDateConverter.formatBsDate(bsDate, 'YYYY MMMM DD', useUnicode);
            return `${adFormatted} (${bsFormatted})`;
        }
    } catch (error) {
        console.error("Error formatting date with BS:", error);
    }

    return adFormatted;
}

/**
 * Format datetime for list view with both AD and BS
 */
export function formatDateTimeWithBs(value, options = {}) {
    if (!value) return '';

    const adFormatted = options.showTime === false
        ? _formatDate(value, options)
        : _formatDateTime(value, options);

    try {
        const dateObj = new Date(value);
        const bsDate = nepaliDateConverter.adToBs(dateObj);

        if (bsDate) {
            const useUnicode = shouldUseUnicode();
            const bsFormatted = nepaliDateConverter.formatBsDate(bsDate, 'YYYY MMMM DD', useUnicode);
            return `${adFormatted} (${bsFormatted})`;
        }
    } catch (error) {
        console.error("Error formatting datetime with BS:", error);
    }

    return adFormatted;
}

// Initialize settings on module load
(async () => {
    try {
        await loadSettings();
        console.log('[Nepali Calendar Enhanced] Settings initialized successfully');
    } catch (error) {
        console.error('[Nepali Calendar Enhanced] Failed to initialize settings:', error);
    }
})();

// Register the formatters
registry.category("formatters").remove("datetime");
registry.category("formatters").remove("date");

// Register formatters that use backend settings
registry.category("formatters").add("datetime", myformatDateTime);
registry.category("formatters").add("date", myformatDate);

console.log('[Nepali Calendar Enhanced] Date formatters registered successfully with settings backend');

// Add a global helper to check current status
window.nepaliCalendarDebug = {
    checkMode: async () => {
        const settings = await loadSettings();
        console.log('=== Nepali Calendar Status (Backend Settings) ===');
        console.log('Enabled:', settings.enable);
        console.log('Date Format:', settings.date_format);
        console.log('DateTime Format:', settings.datetime_format);
        console.log('Date Pattern:', settings.date_pattern);
        console.log('DateTime Pattern:', settings.datetime_pattern);
        console.log('Calendar Mode:', settings.calendar_mode);
        console.log('Should show BS (date):', settings.enable && settings.date_format !== 'ad_only');
        console.log('Should show BS (datetime):', settings.enable && settings.datetime_format !== 'ad_only');
        return settings;
    },
    reloadSettings: async () => {
        _cachedSettings = null;
        _settingsPromise = null;
        const settings = await loadSettings();
        console.log('Settings reloaded from backend:', settings);
        console.log('Please refresh the page to apply new settings to all views');
        return settings;
    },
    testConversion: (adDate = '2024-11-27') => {
        const dateObj = new Date(adDate);
        const bsDate = nepaliDateConverter.adToBs(dateObj);
        console.log('AD Date:', adDate);
        console.log('BS Date:', bsDate);
        console.log('Formatted (English):', nepaliDateConverter.formatBsDate(bsDate, 'YYYY MMMM DD', false));
        console.log('Formatted (Unicode):', nepaliDateConverter.formatBsDate(bsDate, 'YYYY MMMM DD', true));
        return bsDate;
    },
    testFormatter: (adDate = '2024-11-27') => {
        console.log('Testing formatters with date:', adDate);
        console.log('Date formatter:', myformatDate(adDate));
        console.log('DateTime formatter:', myformatDateTime(adDate));
        return { date: myformatDate(adDate), datetime: myformatDateTime(adDate) };
    }
};
