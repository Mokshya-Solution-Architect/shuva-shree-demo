/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * Nepali Calendar Settings Service
 * Fetches and caches settings from backend
 */
export const nepaliCalendarService = {
    dependencies: [],

    async start() {
        let settings = null;
        let isLoading = false;
        let loadPromise = null;

        /**
         * Load settings from backend
         */
        async function loadSettings() {
            if (isLoading) {
                return loadPromise;
            }

            isLoading = true;
            loadPromise = rpc('/nepali_calendar/get_settings').then((result) => {
                console.log('[Nepali Calendar] Settings loaded from backend:', result);

                settings = result;
                isLoading = false;

                console.log('[Nepali Calendar] Processed settings:', settings);
                return settings;
            }).catch((error) => {
                console.error('[Nepali Calendar] Failed to load settings:', error);
                // Return defaults on error
                settings = {
                    enable: false,
                    date_format: 'ad_only',
                    date_pattern: 'YYYY-MM-DD',
                    datetime_format: 'ad_only',
                    calendar_mode: 'ad',
                    show_in_reports: false
                };
                isLoading = false;
                console.log('[Nepali Calendar] Using default settings:', settings);
                return settings;
            });

            return loadPromise;
        }

        /**
         * Get settings (load if not cached)
         */
        async function getSettings() {
            if (!settings) {
                await loadSettings();
            }
            return settings;
        }

        /**
         * Reload settings from backend
         */
        async function reloadSettings() {
            settings = null;
            return loadSettings();
        }

        /**
         * Check if Nepali calendar is enabled
         */
        async function isEnabled() {
            const config = await getSettings();
            return config.enable;
        }

        /**
         * Get calendar mode setting
         */
        async function getCalendarMode() {
            const config = await getSettings();
            return config.calendar_mode;
        }

        /**
         * Get date format setting
         */
        async function getDateFormat() {
            const config = await getSettings();
            return config.date_format;
        }

        /**
         * Get date pattern setting
         */
        async function getDatePattern() {
            const config = await getSettings();
            return config.date_pattern;
        }

        /**
         * Get datetime format setting
         */
        async function getDateTimeFormat() {
            const config = await getSettings();
            return config.datetime_format;
        }

        /**
         * Should use Unicode (Nepali numerals)?
         */
        async function shouldUseUnicode() {
            const config = await getSettings();
            return config.date_format === 'bs_unicode' || config.datetime_format === 'bs_unicode';
        }

        /**
         * Should show B.S dates in reports?
         */
        async function showInReports() {
            const config = await getSettings();
            return config.show_in_reports;
        }

        return {
            getSettings,
            reloadSettings,
            isEnabled,
            getCalendarMode,
            getDateFormat,
            getDatePattern,
            getDateTimeFormat,
            shouldUseUnicode,
            showInReports,
        };
    },
};

registry.category("services").add("nepali_calendar", nepaliCalendarService);
