import logging
import requests
import json
import random
import string
import time
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pss
from base64 import b64encode, b64decode

_logger = logging.getLogger(__name__)


class PaymentMethod(models.Model):
    _inherit = 'payment.method'

    def _detect_app_from_request(self):
        """Detect if request is from Telebirr or Dashen super app"""
        if not request:
            return None

        # Method 1: X-Requested-With header (Android apps)
        requested_with = request.httprequest.headers.get('X-Requested-With', '').lower()
        if 'dashen' in requested_with or 'dashensuperapp' in requested_with:
            _logger.info("Super app detected: Dashen (via X-Requested-With)")
            return 'dashin'
        elif 'ethiopay' in requested_with or 'tydic' in requested_with or 'telebirr' in requested_with:
            _logger.info("Super app detected: Telebirr (via X-Requested-With)")
            return 'telebirr'

        # Method 2: URL Parameters (iOS apps)
        url = str(request.httprequest.url).lower()
        if 'app=dashin' in url or 'app=dashen' in url:
            _logger.info("Super app detected: Dashen (via URL parameter)")
            return 'dashin'
        elif 'app=telebirr' in url or 'app=ethiopay' in url:
            _logger.info("Super app detected: Telebirr (via URL parameter)")
            return 'telebirr'

        # Method 3: Request params
        if hasattr(request, 'params') and request.params:
            app_param = request.params.get('app', '').lower()
            if app_param in ['dashin', 'dashen']:
                _logger.info("Super app detected: Dashen (via request params)")
                return 'dashin'
            elif app_param in ['telebirr', 'ethiopay']:
                _logger.info("Super app detected: Telebirr (via request params)")
                return 'telebirr'

        # Method 4: Referer analysis
        referer = request.httprequest.headers.get('Referer', '').lower()
        if 'app=dashin' in referer or 'app=dashen' in referer:
            _logger.info("Super app detected: Dashen (via Referer)")
            return 'dashin'
        elif 'app=telebirr' in referer or 'ethiopay' in referer:
            _logger.info("Super app detected: Telebirr (via Referer)")
            return 'telebirr'

        # Method 5: Telebirr-specific parameters
        if any(param in url for param in ['language=', 'version=', 'platform=', 'apksign=']):
            _logger.info("Super app detected: Telebirr (via Telebirr-specific URL params)")
            return 'telebirr'
        if any(param in referer for param in ['language=', 'version=', 'platform=', 'apksign=']):
            _logger.info("Super app detected: Telebirr (via Telebirr-specific Referer params)")
            return 'telebirr'

        _logger.info("No super app detected - normal browser/QR scanner")
        return None

    def _get_compatible_payment_methods(
            self, provider_ids, partner_id, currency_id=None, force_tokenization=False,
            is_express_checkout=False, **kwargs
        ):
        """Filter payment methods: hide payment_telebirr when NO super app is detected"""

        _logger.info("=== Payment Telebirr Method Filtering ===")
        _logger.info("Provider IDs: %s", provider_ids)

        # Detect if request is from a super app
        detected_app = self._detect_app_from_request()

        # Get payment_telebirr provider
        telebirr_inline_provider = self.env['payment.provider'].search([('code', '=', 'telebirr')], limit=1)

        if not telebirr_inline_provider:
            _logger.warning("payment_telebirr provider not found, using default behavior")
            return super()._get_compatible_payment_methods(
                provider_ids, partner_id, currency_id, force_tokenization, is_express_checkout, **kwargs
            )

        # If payment_telebirr is in the provider_ids
        if telebirr_inline_provider.id in provider_ids:
            if not detected_app:
                # No super app detected → HIDE payment_telebirr (remove it from provider_ids)
                _logger.info("No super app detected → Hiding payment_telebirr (inline) payment method")
                provider_ids = [pid for pid in provider_ids if pid != telebirr_inline_provider.id]
            else:
                # Super app detected → SHOW payment_telebirr
                _logger.info("Super app '%s' detected → Showing payment_telebirr (inline) payment method", detected_app)

        # Call parent method with filtered provider_ids
        return super()._get_compatible_payment_methods(
            provider_ids, partner_id, currency_id, force_tokenization, is_express_checkout, **kwargs
        )


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    receivable_account_id = fields.Many2one(
        'account.account',
        string='Intermediary Account',
        required=False,  # Set to False to make it optional
        # domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]"
    )


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    # ------------------------------------------------------------------
    # Telebirr-specific configuration fields (company-dependent)
    # ------------------------------------------------------------------

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=False,
        readonly=False
    )
    branch_id = fields.Many2many(
        'res.company',
        string='Branches',
        required=False,
        readonly=False,
        domain=lambda self: "[('id', 'in', parent.company_id.child_ids.ids)]" if self.company_id else "[]",
        help="The company branches associated with this payment provider configuration."
    )
    code = fields.Selection(
        selection_add=[('telebirr', 'Telebirr')],
        ondelete={'telebirr': 'set default'},
    )
    aggregator_payer_id = fields.Integer(
        string="Aggregator Payer ID",
        help="Identifier given by the aggregator that proxies Telebirr requests for these branches."
    )
    domain = fields.Char(
        string="Create-order endpoint",
        default="https://pgw.shekla.app/telebirr/h5/create_order",
        help="Full URL of the H5 create_order endpoint exposed by the aggregator or Telebirr for these branches."
    )
    telebirr_api_key = fields.Char(
        string='Telebirr API Key',
        groups='base.group_user',
        help="Secret token delivered by the aggregator for these branches."
    )


    fabricAppId = fields.Char(
        string="Fabric App ID",
        required_if_provider='telebirr',
        groups='base.group_system'
    )
    appSecret = fields.Char(
        string="App Secret",
        required_if_provider='telebirr',
        groups='base.group_system'
    )
    merchantAppId = fields.Char(
        string="Merchant App ID",
        required_if_provider='telebirr',
        groups='base.group_system'
    )
    merchantCode = fields.Char(
        string="Merchant Code",
        required_if_provider='telebirr',
        groups='base.group_system'
    )
    privateKey = fields.Char(
        string="Private Key",
        required_if_provider='telebirr',
        groups='base.group_system'
    )

    # ------------------------------------------------------------------
    # Query API Configuration (Additional - does not affect callback)
    # ------------------------------------------------------------------
    base_url = fields.Char(
        string="Telebirr Base URL",
        default="https://api.ethiotelecom.et",
        help="Base URL for Telebirr Fabric API (used for query mode)"
    )
    payment_check_mode = fields.Selection([
        ('callback', 'Callback Mode (Wait for Webhook)'),
        ('query', 'Query Mode (Poll Telebirr API)')
    ], string="Payment Check Mode", default='callback',
        help="Callback Mode: Wait for Telebirr webhook notification (existing behavior).\n"
             "Query Mode: Poll Telebirr API to check payment status.")

    # Token caching fields (for query mode)
    cached_fabric_token = fields.Char(string="Cached Fabric Token", copy=False)
    token_expiration_date = fields.Char(string="Token Expiration Date", copy=False)

    # ------------------------------------------------------------------
    # Low-level HTTP helper – JSON only (all Telebirr endpoints speak JSON)
    # ------------------------------------------------------------------
    def _telebirr_make_request(self, url, payload):
        """POST *payload* to *url* and return a python dict.

        Adds the content-type and X-API-KEY headers automatically.
        """

        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.telebirr_api_key or "",
        }
        self.ensure_one()
        _logger.info("Telebirr ▶ POST %s  headers=%s  body=%s", url, headers, payload)

        try:
            r = requests.post(url, json=payload, timeout=20, headers=headers)
            r.raise_for_status()
        except Exception as exc:
            _logger.error("Telebirr HTTP error: %s", exc, exc_info=True)
            raise ValidationError(_("Could not reach Telebirr gateway (%s)") % exc)

        try:
            data = r.json()
        except ValueError:
            _logger.error("Telebirr did not return JSON: %s", r.text[:300])
            raise ValidationError(_("Telebirr gateway sent invalid JSON"))

        _logger.info("Telebirr ◀ %s", data)
        return data

    # ------------------------------------------------------------------
    # Query API Methods (Additional - does not affect callback)
    # ------------------------------------------------------------------

    def _create_nonce_str(self, length=32):
        """Generate a random nonce string."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def _create_timestamp(self):
        """Generate a timestamp."""
        return str(int(time.time()))

    def _is_token_expired(self, expiration_date_str):
        """Check if token is expired based on Telebirr's expirationDate format (YYYYMMDDHHmmss)."""
        if not expiration_date_str:
            return True
        try:
            from datetime import datetime
            exp_date = datetime.strptime(expiration_date_str, "%Y%m%d%H%M%S")
            now = datetime.now()
            buffer_seconds = 300  # 5 minutes buffer
            is_expired = (exp_date.timestamp() - buffer_seconds) <= now.timestamp()
            _logger.info("Token expiration check: exp_date=%s, now=%s, expired=%s", exp_date, now, is_expired)
            return is_expired
        except Exception as e:
            _logger.error("Error parsing token expiration date: %s", str(e))
            return True

    def _telebirr_apply_fabric_token(self):
        """Retrieve Fabric Token from Telebirr API."""
        self.ensure_one()
        _logger.info("Applying Fabric Token with base_url: %s, fabricAppId: %s", self.base_url, self.fabricAppId)

        headers = {
            "Content-Type": "application/json",
            "X-APP-Key": self.fabricAppId,
        }
        payload = {"appSecret": self.appSecret}

        try:
            response = requests.post(
                url=f"{self.base_url}/payment/v1/token",
                headers=headers,
                json=payload,
                timeout=20,
                verify=False,
            )
            response.raise_for_status()
            response_json = response.json()
            _logger.info("Fabric Token response: %s", response_json)
            return response_json
        except requests.exceptions.RequestException as e:
            _logger.error("Error during applyFabricToken request: %s", str(e))
            return {"error": str(e)}

    def _telebirr_get_cached_or_new_token(self):
        """Get cached token if valid, otherwise fetch new token and cache it."""
        self.ensure_one()
        _logger.info("Getting fabric token (cached or new)")

        # Check if we have a valid cached token
        if self.cached_fabric_token and self.token_expiration_date:
            if not self._is_token_expired(self.token_expiration_date):
                _logger.info("Using cached fabric token (expires: %s)", self.token_expiration_date)
                return {'token': self.cached_fabric_token}
            else:
                _logger.info("Cached token expired, fetching new one")

        # Fetch new token
        token_result = self._telebirr_apply_fabric_token()

        # Cache the new token if successful
        if 'token' in token_result:
            try:
                self.sudo().write({
                    'cached_fabric_token': token_result['token'],
                    'token_expiration_date': token_result.get('expirationDate', '')
                })
                _logger.info("Cached new fabric token (expires: %s)", token_result.get('expirationDate'))
            except Exception as e:
                _logger.warning("Could not cache token: %s", str(e))

        return token_result

    def _telebirr_sign_with_rsa(self, data):
        """Perform RSA signing with SHA256."""
        self.ensure_one()
        _logger.info("Performing RSA signing")

        try:
            key_bytes = b64decode(self.privateKey.encode("utf-8"))
            rsa_key = RSA.importKey(key_bytes)
            digest = SHA256.new(data.encode("utf-8"))
            signer = pss.new(rsa_key)
            signature = signer.sign(digest)
            encoded_signature = b64encode(signature).decode("utf-8")
            return encoded_signature
        except Exception as e:
            _logger.error("RSA signing error: %s", str(e))
            raise ValidationError(_("RSA signing failed: %s") % str(e))

    def _telebirr_sign_request(self, request_obj):
        """Sign the request object with RSA."""
        self.ensure_one()
        exclude_fields = ["sign", "sign_type", "header", "refund_info", "openType", "raw_request"]
        join = []

        for key in request_obj:
            if key in exclude_fields:
                continue
            if key == "biz_content":
                for k, v in request_obj["biz_content"].items():
                    join.append(f"{k}={str(v)}")
            else:
                join.append(f"{key}={str(request_obj[key])}")

        join.sort()
        input_string = '&'.join(join)
        _logger.info("Input string for signing: %s", input_string)

        signature = self._telebirr_sign_with_rsa(input_string)
        _logger.info("Generated signature: %s", signature)
        return signature

    def _telebirr_query_order(self, merch_order_id):
        """Query Telebirr API for payment status.

        Args:
            merch_order_id: The merchant order ID to query

        Returns:
            dict: Query result from Telebirr API
        """
        self.ensure_one()
        _logger.info("Querying Telebirr order status for merch_order_id: %s", merch_order_id)

        # Get fabric token
        token_result = self._telebirr_get_cached_or_new_token()
        if 'error' in token_result:
            return {"success": False, "message": f"Failed to get fabric token: {token_result['error']}"}

        fabric_token = token_result.get('token')
        if not fabric_token:
            return {"success": False, "message": "Failed to get fabric token"}

        # Build request object
        req = {
            "timestamp": self._create_timestamp(),
            "nonce_str": self._create_nonce_str(),
            "method": "payment.queryorder",
            "version": "1.0",
            "biz_content": {
                "appid": self.merchantAppId,
                "merch_code": self.merchantCode,
                "merch_order_id": merch_order_id,
            }
        }

        # Sign the request
        req["sign"] = self._telebirr_sign_request(req)
        req["sign_type"] = "SHA256WithRSA"

        # Make the query request
        url = f"{self.base_url}/payment/v1/merchant/queryOrder"
        headers = {
            "Content-Type": "application/json",
            "X-APP-Key": self.fabricAppId,
            "Authorization": fabric_token,
        }

        _logger.info("Query order request URL: %s", url)
        _logger.info("Query order request: %s", json.dumps(req, indent=2))

        try:
            response = requests.post(url, json=req, headers=headers, timeout=20, verify=False)
            response.raise_for_status()
            result = response.json()
            _logger.info("Query order response: %s", result)
            return result
        except requests.exceptions.RequestException as e:
            _logger.error("Query order request failed: %s", str(e))
            return {"success": False, "message": f"Request failed: {str(e)}"}
