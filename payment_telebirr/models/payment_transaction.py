# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError
from odoo.tools import html_escape
from datetime import datetime, timezone
import json, re, logging, pprint, base64, hashlib

_logger = logging.getLogger(__name__)

MAX_TRACE_LEN = 32 

# ---------------------------------------------------------------------------
# helper: translate Telebirr trade_status → Odoo tx state buckets
TRANSACTION_STATUS_MAPPING = {
    "done":     {"Completed"},
    "pending":  {"Pending", "Processing"},
    "canceled": {"Failed", "Canceled"},
}
# ---------------------------------------------------------------------------

class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    # store a few callback fields (optional – add them to the tree/form view if desired)
    telebirr_trade_status   = fields.Char(readonly=True)
    telebirr_merch_order_id = fields.Char(readonly=True)
    telebirr_payment_order_id = fields.Char(readonly=True)
    telebirr_trans_id       = fields.Char(readonly=True)

    # =========================================================================
    #  Telebirr helpers
    # =========================================================================
    def _telebirr_create_remote_order(self):
        """
        Send the pre-order to your aggregator  ➜  receive `rawRequest`.
        Also create an entry in telebirr.order.mapping so that callbacks
        (which only know merch_order_id) can find the correct tx+db later.
        """
        self.ensure_one()
        if self.provider_code != "telebirr":
            return False

        # ────────────────────────────────────────────────────────
        #  1. db-prefix  (letters & digits only)
        # ────────────────────────────────────────────────────────
        db_prefix = re.sub(r"[^A-Za-z0-9]", "", self.env.cr.dbname).upper()[:8]  # e.g. "NAMETEST"
        prefix = f"{db_prefix}H5QR"
        
        # ────────────────────────────────────────────────────────
        #  2. traceNo   (prefix + cleaned reference + 8-digit nonce)
        #      * alphanumeric only
        #      * ≤ 32 chars
        # ────────────────────────────────────────────────────────
        ref_clean = re.sub(r"[^A-Za-z0-9]", "", self.reference)
        nonce     = datetime.now(timezone.utc).strftime("%H%M%S%f")[-8:]

        room      = 32 - len(prefix) - len(nonce)          # 32 is spec limit
        trace_no  = f"{prefix}{ref_clean[:room]}{nonce}"   # unique, ≤32 chars
        _logger.info("💡 Telebirr traceNo generated → %s", trace_no)

        # ────────────────────────────────────────────────────────
        #  3. title  (prefix + original reference, max 40 chars,
        #             strip disallowed punctuation)
        # ────────────────────────────────────────────────────────
        raw_title = f"{prefix} {self.reference}"
        title_clean = re.sub(r'[~`!#$%^*()\-+=|/<>?;:"\[\]{}\\&]', "", raw_title)[:40] or "Payment"
        _logger.info("💡 Telebirr title generated  → %s", title_clean)
        base_url = self.provider_id.get_base_url().replace('http://', 'https://', 1)
        notifyUrl = f"{base_url}telebirr/h5/merchant_callback"
        payload = {
            # "payerId":     self.provider_id.aggregator_payer_id,
            "traceNo":     trace_no,
            "amount":      f"{self.amount:.2f}",
            "fabricAppId": self.provider_id.fabricAppId,
            "appSecret": self.provider_id.appSecret,
            "redirectUrl": f"{self.provider_id.get_base_url()}payment/telebirr/return",
            # "notifyUrl":   f"{self.provider_id.get_base_url()}telebirr/h5/merchant_callback",
            # "notifyUrl":   f"https://demo.zoorya.et/telebirr/h5/merchant_callback",
            'notifyUrl':notifyUrl,

            "title":       html_escape(title_clean),
            "merchantCode": self.provider_id.merchantCode,
            "merchantAppId": self.provider_id.merchantAppId,
            "privateKey": self.provider_id.privateKey,

        }
        _logger.info("Telebirr payload → %s", payload)

        # ===== real call =====================================================
        resp = self.provider_id._telebirr_make_request(
            self.provider_id.domain, payload
        )

        # accepted response shapes:
        #   {"rawRequest": "..."}
        #   {"jsonrpc":"2.0","result":{"rawRequest":"..."}}
        raw = None
        if isinstance(resp, dict):
            raw = resp.get("rawRequest") or resp.get("result", {}).get("rawRequest")

        if not raw:
            raise ValidationError(_("Telebirr gateway did not return a rawRequest"))

        _logger.info("rawRequest received (%s chars)", len(raw))
        # ---- remember mapping for the callback --------------------------------
        # self.env["telebirr.order.mapping"].sudo().create({
        #     "merch_order_id": trace_no,          # Telebirr later echoes *our* traceNo
        #     "original_reference": self.reference,
        #     "db_name": self.env.cr.dbname,
        # })
        mapping_model = self.env['telebirr.order.mapping'].sudo()

        existing = mapping_model.search([('merch_order_id', '=', trace_no)], limit=1)
        if existing:
            _logger.info("Found existing mapping for %s – re-using it", trace_no)
        else:
            mapping_model.create({
                'merch_order_id': trace_no,
                'original_reference': self.reference,
                'db_name': self.env.cr.dbname,
                'tx_id': self.id,
            })

        return raw

    # -----------------------------------------------------------------------
    #  Odoo hooks
    # -----------------------------------------------------------------------
    def _get_specific_processing_values(self, processing_values):
        vals = super()._get_specific_processing_values(processing_values)
        if self.provider_code != "telebirr":
            return vals

        raw = self._telebirr_create_remote_order()

        telebirr_vals = {
            "rawRequest":  raw,
            "provider_id": self.provider_id.id,
            "reference":   self.reference,
            "amount":      float(self.amount),
        }
        vals.update(telebirr_vals)
        # store a JSON dump for the template
        vals["telebirr_vals_json"] = json.dumps(telebirr_vals)
        return vals

    def _get_specific_rendering_values(self, processing_values):
        vals = super()._get_specific_rendering_values(processing_values)
        if self.provider_code == "telebirr":
            vals.update({"telebirr_vals_json": processing_values["telebirr_vals_json"]})
        return vals


    # ------------------------------------------------------------------------
    #  Call-back helpers
    # ------------------------------------------------------------------------
    def _telebirr_verify_signature(self, data):
        """
        Stub – fill in real RSA/SHA-256 verification if/when Telebirr
        requires it.  Return True / False.
        """
        sign = data.get("sign")
        if not sign:
            return False
        #  -- your PKI here --
        return True

    # override of payment to *find* the transaction ---------------------------
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        if provider_code != "telebirr":
            return super()._get_tx_from_notification_data(provider_code, notification_data)

        # This is a telebirr notification

        merch_order_id = notification_data.get("merch_order_id") or notification_data.get("traceNo")
        if not merch_order_id:
            raise ValidationError(_("Telebirr: missing merch_order_id / traceNo"))

        mapping = self.env["telebirr.order.mapping"].sudo().search(
            [("merch_order_id", "=", merch_order_id)], limit=1
        )
        if not mapping:
            raise ValidationError(_("Telebirr: unknown Merchant Order ID %s") % merch_order_id)

        tx = self.search([
            ("reference", "=", mapping.original_reference),
            ("provider_code", "=", "telebirr"),
        ], limit=1)

        if not tx:
            raise ValidationError(_("Telebirr: no transaction for reference %s") %
                                  mapping.original_reference)
        return tx

    # override to *apply* the notification ------------------------------------
    def _process_notification_data(self, notification_data):
        if self.provider_code != "telebirr":
            return super()._process_notification_data(notification_data)

        # This is a telebirr notification - process it

        if not self._telebirr_verify_signature(notification_data):
            raise ValidationError(_("Telebirr: invalid signature"))

        # keep the raw fields (handy for support)
        self.write({
            "telebirr_trade_status":   notification_data.get("trade_status"),
            "telebirr_merch_order_id": notification_data.get("merch_order_id"),
            "telebirr_payment_order_id": notification_data.get("payment_order_id"),
            "telebirr_trans_id":       notification_data.get("trans_id"),
        })

        status = notification_data.get("trade_status")
        if status in TRANSACTION_STATUS_MAPPING["done"]:
            _logger.info("Telebirr payment successful (order %s)", self.telebirr_payment_order_id)
            self._set_done()
        elif status in TRANSACTION_STATUS_MAPPING["pending"]:
            _logger.info("Telebirr payment pending")
            self._set_pending()
        elif status in TRANSACTION_STATUS_MAPPING["canceled"]:
            _logger.info("Telebirr payment canceled/failed")
            self._set_canceled()
        else:
            _logger.warning("Telebirr: unknown status %s for tx %s", status, self.reference)
            self._set_error()