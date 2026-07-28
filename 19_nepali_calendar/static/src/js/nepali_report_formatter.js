/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { nepaliDateConverter } from "./nepali_date_converter";
import { _t } from "@web/core/l10n/translation";

/**
 * Format date for reports with BS support
 * This ensures printed reports show BS dates when in BS mode
 */

// Get user preferences
function shouldShowBsDate() {
    const savedMode = browser.localStorage.getItem('nepali_calendar_mode');
    console.log('[Report] BS Mode:', savedMode === 'bs');
    return savedMode === 'bs';
}

function shouldUseUnicode() {
    const savedUnicode = browser.localStorage.getItem('nepali_unicode_mode');
    return savedUnicode === 'true';
}

/**
 * Convert any date value to BS formatted string
 */
export function formatDateForReport(dateValue) {
    if (!dateValue) return '';

    try {
        // Handle different date formats
        let dateObj;
        if (dateValue instanceof Date) {
            dateObj = dateValue;
        } else if (typeof dateValue === 'string') {
            dateObj = new Date(dateValue);
        } else if (dateValue.toJSDate) {
            // Luxon DateTime
            dateObj = dateValue.toJSDate();
        } else {
            dateObj = new Date(dateValue);
        }

        // Check if we should show BS
        if (shouldShowBsDate()) {
            const bsDate = nepaliDateConverter.adToBs(dateObj);
            if (bsDate) {
                const useUnicode = shouldUseUnicode();
                return nepaliDateConverter.formatBsDate(bsDate, 'YYYY MMMM DD', useUnicode);
            }
        }

        // Fallback to AD format
        return dateObj.toLocaleDateString();
    } catch (error) {
        console.error('[Report] Error formatting date:', error);
        return String(dateValue);
    }
}

// Make it globally available for QWeb templates
window.formatDateForReport = formatDateForReport;

// Also export for use in JavaScript
export default {
    formatDateForReport,
    shouldShowBsDate,
    shouldUseUnicode,
};

console.log('[Nepali Calendar] Report formatter loaded');
