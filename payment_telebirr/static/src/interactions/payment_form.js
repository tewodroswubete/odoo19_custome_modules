/** @odoo-module */
/* global consumerapp */

import { patch } from '@web/core/utils/patch';
import { PaymentForm } from '@payment/interactions/payment_form';

patch(PaymentForm.prototype, {

    // #=== DOM MANIPULATION ===#

    /**
     * Prepare the inline form of Telebirr for direct payment.
     *
     * @override method from @payment/interactions/payment_form
     * @private
     * @param {number} providerId - The id of the selected payment option's provider.
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {string} flow - The online payment flow of the selected payment option.
     * @return {void}
     */
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'telebirr') {
            await super._prepareInlineForm(...arguments);
            return;
        } else if (flow === 'token') {
            return;
        }

        const script = document.querySelector(
            '.o_telebirr_inline_form script[name="telebirr_data"]'
        );
        this.telebirrData = JSON.parse((script?.textContent || "{}").trim());
        console.log("[Telebirr] inline JSON =", this.telebirrData);

        this._setPaymentFlow('direct');
    },

    // #=== PAYMENT FLOW ===#

    /**
     * Process the Telebirr payment using the consumerapp interface.
     *
     * @override method from @payment/interactions/payment_form
     * @private
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {object} processingValues - The processing values of the transaction.
     * @return {void}
     */
    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'telebirr') {
            await super._processDirectFlow(...arguments);
            return;
        }

        console.log("[Telebirr] processingValues =", processingValues);

        const raw = (processingValues.rawRequest || "").trim();
        if (!raw) {
            this._displayErrorDialog("Telebirr", "rawRequest missing – cannot start payment.");
            this._enableButton();
            return;
        }

        // Check if we're inside Telebirr super-app
        if (!window.consumerapp || typeof consumerapp.evaluate !== "function") {
            console.warn("[Telebirr] NOT inside super-app — rawRequest =\n", raw);

            this._displayErrorDialog(
                "Telebirr",
                `Please open this page inside the Telebirr super-app.\n\n` +
                `Debug rawRequest:\n${raw}`
            );
            this._enableButton();
            return;
        }

        // Setup callback for payment completion
        window.handleinitDataCallback = () => {
            console.log("[Telebirr] callback received – redirecting to /payment/status");
            window.location = "/payment/status";
        };

        try {
            console.log("[Telebirr] calling consumerapp.evaluate");
            consumerapp.evaluate(JSON.stringify({
                functionName: "js_fun_start_pay",
                params: {
                    rawRequest: raw,
                    functionCallBackName: "handleinitDataCallback",
                },
            }));
        } catch (err) {
            console.error("[Telebirr] evaluate error:", err);
            this._displayErrorDialog("Telebirr", err.message || "Could not start payment");
            this._enableButton();
        }
    },

});
