# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = 'pos.session'

    active_waiter_ids = fields.Many2many(
        'res.users',
        'pos_session_waiter_rel',
        'session_id',
        'waiter_id',
        string='Active Waiters',
        help='Waiters currently logged in to this session'
    )

    waiter_count = fields.Integer(
        string='Number of Waiters',
        compute='_compute_waiter_count',
        store=True,
    )

    @api.depends('active_waiter_ids')
    def _compute_waiter_count(self):
        for session in self:
            session.waiter_count = len(session.active_waiter_ids)

    @api.model
    def get_active_session_for_waiter(self, config_id=None):
        """
        Get the currently active POS session for waiter to connect to
        Returns session data needed by waiter screen
        """
        domain = [('state', '=', 'opened')]

        if config_id:
            domain.append(('config_id', '=', config_id))
        else:
            # Get any restaurant POS config with open session
            domain.append(('config_id.module_pos_restaurant', '=', True))

        session = self.search(domain, limit=1)

        if not session:
            raise UserError(_(
                'No active POS session found. Please ask the manager to open a session first.'
            ))

        return {
            'id': session.id,
            'name': session.name,
            'config_id': session.config_id.id,
            'config_name': session.config_id.name,
            'start_at': session.start_at,
            'user_id': session.user_id.id,
        }

    def waiter_login(self, waiter_id=None):
        """
        Register waiter to active session
        Called when waiter logs in to waiter screen
        """
        self.ensure_one()

        if self.state != 'opened':
            raise UserError(_('This POS session is not open'))

        waiter_id = waiter_id or self.env.user.id
        waiter = self.env['res.users'].browse(waiter_id)

        # Add waiter to active list if not already there
        if waiter not in self.active_waiter_ids:
            self.write({
                'active_waiter_ids': [(4, waiter_id)]
            })

        return True

    def waiter_logout(self, waiter_id=None):
        """
        Remove waiter from active session
        Called when waiter logs out
        """
        self.ensure_one()

        waiter_id = waiter_id or self.env.user.id

        # Remove waiter from active list
        if waiter_id in self.active_waiter_ids.ids:
            self.write({
                'active_waiter_ids': [(3, waiter_id)]
            })

        return True

    @api.model
    def get_waiter_session_data(self):
        """
        Get all data needed for waiter screen
        Similar to _load_pos_data but lighter
        """
        session = self.get_active_session_for_waiter()
        session_obj = self.browse(session['id'])

        # Load necessary data
        data = {
            'session': session,
            'config': session_obj.config_id.read([
                'name', 'floor_ids', 'module_pos_restaurant'
            ])[0],
            'payment_methods': session_obj.config_id.payment_method_ids.read([
                'name', 'type'
            ]),
            'floors': session_obj.config_id.floor_ids.read([
                'name', 'background_color', 'sequence', 'table_ids'
            ]),
            'tables': self.env['restaurant.table'].get_tables_status(
                floor_ids=session_obj.config_id.floor_ids.ids
            ),
            'categories': self.env['pos.category'].search([]).read([
                'name', 'parent_id', 'sequence'
            ]),
            'products': self.env['product.product'].search([
                ('available_in_pos', '=', True)
            ]).read([
                'name', 'list_price', 'pos_categ_ids',
                'uom_id', 'taxes_id', 'image_128'
            ]),
        }

        return data
