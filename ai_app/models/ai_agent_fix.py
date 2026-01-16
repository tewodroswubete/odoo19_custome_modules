# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AIAgentFix(models.Model):
    _inherit = 'ai.agent'

    def _generate_response_for_channel(self, mail_message, channel):
        """Override to show proper error messages for quota issues"""
        self.ensure_one()
        prompt, session_info_context = self._parse_user_message(mail_message)
        try:
            response = self.with_context(discuss_channel=channel)._generate_response(
                prompt=prompt,
                chat_history=[{'content': session_info_context, 'role': 'user'}] + self._retrieve_chat_history(channel),
                extra_system_context=self._build_extra_system_context(channel),
            )
        except UserError as e:
            # Handle specific API errors with clear messages
            error_msg = str(e)

            # Check for quota errors
            if 'quota' in error_msg.lower() or 'billing' in error_msg.lower():
                response = [_("⚠️ API quota exceeded. Please check your API key credits and billing details.")]
            elif 'api key' in error_msg.lower():
                response = [_("⚠️ API key issue. Please verify your API key configuration in Settings.")]
            elif 'rate limit' in error_msg.lower():
                response = [_("⚠️ Rate limit reached. Please wait a moment and try again.")]
            else:
                # For other UserErrors, show a more informative message
                if self.env.user._is_internal():
                    # Internal users get the full error
                    response = [_("⚠️ Error: %s") % error_msg]
                else:
                    # External users get a generic but informative message
                    response = [_("⚠️ The AI service is temporarily unavailable. Please try again later.")]

            _logger.warning("AI API Error: %s", error_msg)

        except Exception as e:
            # For unexpected errors
            _logger.error("Unexpected AI error: %s", str(e), exc_info=True)
            if self.env.user._is_internal():
                # Re-raise for internal users to see full traceback
                raise
            response = [_("⚠️ An unexpected error occurred. Please contact your administrator.")]

        # Post the response (error or success)
        for message in response or []:
            self._post_ai_response(channel, message)