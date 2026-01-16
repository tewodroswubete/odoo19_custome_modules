# -*- coding: utf-8 -*-

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_waiter_screen = fields.Boolean(
        string='Enable Waiter Screen',
        default=True,
        help='Allow waiters to use the dedicated waiter screen interface'
    )

    waiter_screen_url = fields.Char(
        string='Waiter Screen URL',
        compute='_compute_waiter_screen_url',
    )

    def _compute_waiter_screen_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for config in self:
            config.waiter_screen_url = f"{base_url}/pos/waiter"
