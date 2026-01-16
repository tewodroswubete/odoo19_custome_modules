# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class AIAgentDebug(models.Model):
    _inherit = 'ai.agent'

    def _generate_response(self, prompt, chat_history=None, extra_system_context=""):
        """Add debug logging to see what tools are being sent to AI"""

        # Get the tools that will be sent
        tools = self.topic_ids.tool_ids._get_ai_tools()

        _logger.info("="*60)
        _logger.info(f"AI Agent: {self.partner_id.name}")
        _logger.info(f"Model: {self.llm_model}")
        _logger.info(f"Provider: {self._get_provider()}")
        _logger.info(f"Topics: {[t.name for t in self.topic_ids]}")
        _logger.info(f"Number of tools available: {len(tools) if tools else 0}")

        if tools:
            _logger.info(f"Tools: {list(tools.keys())[:10]}")  # Show first 10 tools
        else:
            _logger.warning("⚠️ NO TOOLS AVAILABLE FOR AI!")

        _logger.info(f"User prompt: {prompt[:100]}")
        _logger.info("="*60)

        # Call the original method
        return super()._generate_response(prompt, chat_history, extra_system_context)