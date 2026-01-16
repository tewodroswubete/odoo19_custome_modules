# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    # Override the ai_agent_id field to make it readable for regular users
    # while keeping write access restricted
    ai_agent_id = fields.Many2one(
        "ai.agent",
        index="btree_not_null",
        # Changed from fields.NO_ACCESS to allow read access for all users
        # Write access is still restricted through security rules
        groups="base.group_user",
        readonly=True,
        string="AI Agent"
    )

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """Override search_read to handle ai_agent_id field with sudo when needed"""
        # If ai_agent_id is in the fields list, we need special handling
        if fields and 'ai_agent_id' in fields:
            # First get the records without ai_agent_id
            fields_without_ai = [f for f in fields if f != 'ai_agent_id']
            results = super().search_read(domain, fields_without_ai, offset, limit, order)

            # Then add ai_agent_id using sudo
            if results:
                channel_ids = [r['id'] for r in results]
                channels = self.sudo().browse(channel_ids)
                for i, channel in enumerate(channels):
                    if channel.ai_agent_id:
                        results[i]['ai_agent_id'] = [channel.ai_agent_id.id, channel.ai_agent_id.name]
                    else:
                        results[i]['ai_agent_id'] = False

            return results
        else:
            return super().search_read(domain, fields, offset, limit, order)

    def read(self, fields=None, load='_classic_read'):
        """Override read to handle ai_agent_id field with sudo when needed"""
        if fields and 'ai_agent_id' in fields:
            # Read without ai_agent_id first
            fields_without_ai = [f for f in fields if f != 'ai_agent_id']
            results = super().read(fields_without_ai, load)

            # Add ai_agent_id using sudo
            for i, record_id in enumerate(self.ids):
                channel = self.sudo().browse(record_id)
                if isinstance(results, list):
                    if channel.ai_agent_id:
                        results[i]['ai_agent_id'] = [channel.ai_agent_id.id, channel.ai_agent_id.name] if load == '_classic_read' else channel.ai_agent_id.id
                    else:
                        results[i]['ai_agent_id'] = False

            return results
        else:
            return super().read(fields, load)