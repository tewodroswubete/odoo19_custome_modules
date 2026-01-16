/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Patch to improve AI error handling in the UI
 * This ensures quota errors and other API issues are displayed clearly
 */

// Patch the AI response handler if it exists
if (odoo.ai && odoo.ai.ResponseHandler) {
    patch(odoo.ai.ResponseHandler.prototype, {
        /**
         * Override error handling to show proper messages
         */
        _handleError(error) {
            let message = _t("An error occurred while communicating with the AI.");

            // Parse error message
            const errorStr = error.message || error.toString();

            if (errorStr.includes("quota") || errorStr.includes("billing")) {
                message = _t("⚠️ API quota exceeded. Please check your API key credits and billing details.");
            } else if (errorStr.includes("api key")) {
                message = _t("⚠️ API key issue. Please verify your API key configuration in Settings.");
            } else if (errorStr.includes("rate limit")) {
                message = _t("⚠️ Rate limit reached. Please wait a moment and try again.");
            } else if (errorStr.includes("validation")) {
                // Handle validation errors that might be masking real issues
                message = _t("⚠️ Unable to process request. Please check your API configuration.");
            }

            // Show notification
            this.notification.add(message, {
                type: 'warning',
                sticky: false,
                title: _t("AI Service Issue"),
            });

            // Log for debugging
            console.warn("AI Error:", errorStr);

            return super._handleError ? super._handleError(error) : null;
        }
    });
}

// Also patch JSONRPC error handler for AI endpoints
document.addEventListener('DOMContentLoaded', function() {
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args).then(response => {
            // Check if this is an AI endpoint
            if (args[0] && args[0].includes('/ai/')) {
                // Clone response to read it
                const clonedResponse = response.clone();
                clonedResponse.json().then(data => {
                    if (data.error && data.error.data) {
                        const errorMsg = data.error.data.message || data.error.data.name;

                        // Check for quota errors
                        if (errorMsg && (errorMsg.includes('quota') || errorMsg.includes('billing'))) {
                            // Replace generic validation error with proper quota message
                            if (data.error.data.message) {
                                data.error.data.message = "API quota exceeded. Please check your API key credits.";
                            }
                        }
                    }
                }).catch(() => {
                    // Ignore JSON parse errors
                });
            }
            return response;
        });
    };
});