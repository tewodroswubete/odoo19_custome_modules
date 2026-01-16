# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class AIChatController(http.Controller):
    """
    Controller to ensure AI responses are triggered properly
    """

    @http.route('/ai_app/trigger_response', type='json', auth='user')
    def trigger_ai_response(self, message_id, channel_id):
        """
        Backup trigger for AI response from frontend
        """
        try:
            # Get the channel and verify it's an AI chat
            channel = request.env['discuss.channel'].browse(channel_id)
            if channel.exists() and channel.ai_agent_id:
                # Get the message
                message = request.env['mail.message'].browse(message_id)
                if message.exists():
                    # Trigger AI response
                    channel.sudo().ai_agent_id._generate_response_for_channel(message, channel)
                    return {'success': True}
            return {'success': False, 'error': 'Invalid channel or message'}
        except Exception as e:
            _logger.error(f"Error triggering AI response: {e}")
            return {'success': False, 'error': str(e)}