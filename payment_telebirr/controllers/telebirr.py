# -*- coding: utf-8 -*-
"""
Telebirr H-5 payment-gateway endpoints

* /telebirr/h5/merchant_callback – server-to-server notify  (Telebirr ➜ Odoo)
* /payment/telebirr/return       – browser redirect         (customer ➜ Odoo)
"""
from odoo import api, http, _
from odoo.http import request
import json, logging, pprint, werkzeug

_logger = logging.getLogger(__name__)

class TelebirrController(http.Controller):
    _notify_url = "/telebirr/h5/merchant_callback"
    _return_url = "/payment/telebirr/return"

    # ------------------------------------------------------------------
    # 1) NOTIFY (Telebirr backend ➜ Odoo – no cookies / no session)
    # ------------------------------------------------------------------
    @http.route(_notify_url, type="http", methods=["POST"], auth="public", csrf=False)
    def telebirr_notify(self, **post):
        _logger.info("➡️ Received Telebirr notify request...")

        # ── 0️⃣ Parse payload -------------------------------------------------
        payload = post or {}
        if not payload and request.httprequest.data:
            _logger.info("📦 Raw data detected in request body – attempting JSON decode...")
            try:
                payload = json.loads(request.httprequest.data.decode())
                _logger.info("✅ Successfully parsed JSON body: %s", json.dumps(payload, indent=2))
            except Exception as e:
                _logger.warning("❌ Failed to decode JSON body: %s", str(e))
                return "ERROR"
        else:
            _logger.info("📨 Received payload as POST parameters: %s", pprint.pformat(payload))

        # ── 1️⃣ Extract order ID ---------------------------------------------
        merch_order_id = (
            payload.get("merch_order_id")
            or payload.get("traceNo")
            or payload.get("trace_no")
        )

        if not merch_order_id:
            _logger.error("❌ Missing `merch_order_id` / `traceNo` in Telebirr payload → cannot continue")
            return "ERROR"

        _logger.info("🔍 Extracted merch_order_id: %s", merch_order_id)

        # ── 2️⃣ Begin transaction mapping and processing ---------------------
        try:
            env = request.env

            _logger.info("🔎 Searching for telebirr.order.mapping with merch_order_id = %s", merch_order_id)
            mapping = env["telebirr.order.mapping"].sudo().search([("merch_order_id", "=", merch_order_id)], limit=1)

            if not mapping:
                _logger.error("❌ No mapping found for merch_order_id: %s", merch_order_id)
                return "ERROR"

            _logger.info("✅ Found mapping: %s (ID: %s)", mapping.name if 'name' in mapping else 'N/A', mapping.id)

            # Try to get the transaction
            _logger.info("🔎 Locating payment transaction via _get_tx_from_notification_data...")
            tx = env["payment.transaction"].sudo()._get_tx_from_notification_data("telebirr", payload)

            if not tx:
                _logger.warning("⚠️ No transaction found for merch_order_id: %s", merch_order_id)
            else:
                _logger.info("✅ Found transaction: %s (ID: %s, State: %s)", tx.reference, tx.id, tx.state)

            # Process the transaction
            _logger.info("⚙️ Calling _process_notification_data() to process transaction...")
            tx._process_notification_data(payload)

            # Commit DB changes
            request.env.cr.commit()
            _logger.info("💾 Database committed. Transaction %s now in state: %s", tx.reference, tx.state)

        except Exception as e:
            _logger.exception("💥 Exception during Telebirr notify processing: %s", str(e))
            return "ERROR"

        _logger.info("✅ Telebirr notification handled successfully for merch_order_id: %s", merch_order_id)
        return "OK"


    # ------------------------------------------------------------------
    # 2) QUERY STATUS (Poll Telebirr API for payment status)
    # ------------------------------------------------------------------
    @http.route("/payment/telebirr/query_status", type="jsonrpc", auth="public", methods=["POST"], csrf=False)
    def telebirr_query_status(self, **post):
        """Query Telebirr API for payment status.

        This endpoint is used when payment_check_mode = 'query'.
        It does NOT affect the existing callback functionality.

        Expected POST data:
            - provider_id: ID of the payment.provider record
            - merch_order_id: The merchant order ID to query

        Returns:
            dict: Query result from Telebirr API
        """
        _logger.info("Received Telebirr query status request: %s", post)

        provider_id = post.get('provider_id')
        merch_order_id = post.get('merch_order_id')

        # Validate required parameters
        if not provider_id:
            _logger.error("Missing provider_id in query request")
            return {"success": False, "message": "Missing provider_id"}

        if not merch_order_id:
            _logger.error("Missing merch_order_id in query request")
            return {"success": False, "message": "Missing merch_order_id"}

        try:
            # Get the payment provider
            provider = request.env['payment.provider'].sudo().browse(int(provider_id))
            if not provider.exists():
                _logger.error("Payment provider not found: %s", provider_id)
                return {"success": False, "message": "Payment provider not found"}

            # Check if provider is configured for Telebirr
            if provider.code != 'telebirr':
                _logger.error("Provider is not Telebirr: %s", provider.code)
                return {"success": False, "message": "Provider is not Telebirr"}

            # Query the order status
            result = provider._telebirr_query_order(merch_order_id)
            _logger.info("Query result for %s: %s", merch_order_id, result)

            # If payment is successful, update the transaction
            if result.get("result") == "SUCCESS":
                biz_content = result.get("biz_content", {})
                order_status = biz_content.get("order_status")

                if order_status == "PAY_SUCCESS":
                    # Find and update the transaction
                    mapping = request.env["telebirr.order.mapping"].sudo().search([
                        ("merch_order_id", "=", merch_order_id)
                    ], limit=1)

                    if mapping and mapping.tx_id:
                        tx = mapping.tx_id
                        if tx.state not in ('done', 'cancel', 'error'):
                            _logger.info("Updating transaction %s to done", tx.reference)
                            tx.sudo()._set_done()
                            tx.sudo().write({
                                'telebirr_trade_status': 'Completed',
                                'telebirr_trans_id': biz_content.get('trans_id', '')
                            })
                            result['transaction_updated'] = True

            return result

        except Exception as e:
            _logger.exception("Error in query_status: %s", str(e))
            return {"success": False, "message": f"Internal error: {str(e)}"}

    # ------------------------------------------------------------------
    # 3) RETURN (customer browser – simple redirect)
    # ------------------------------------------------------------------
    # @http.route(_return_url, type="http", auth="public")
    # def telebirr_return(self, **params):
    #     _logger.info("Customer browser returned from Telebirr with params: %s", pprint.pformat(params))
    #     return werkzeug.utils.redirect("/payment/status")