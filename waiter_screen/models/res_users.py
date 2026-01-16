# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessDenied


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_waiter = fields.Boolean(
        string='Is Waiter',
        compute='_compute_is_waiter',
        search='_search_is_waiter',
    )

    waiter_pin = fields.Char(
        string='Waiter PIN',
        size=4,
        help='4-digit PIN for waiter quick login',
    )

    waiter_employee_number = fields.Char(
        string='Employee Number',
        help='Waiter employee identification number',
    )

    def _compute_is_waiter(self):
        waiter_group = self.env.ref('waiter_screen.group_waiter', raise_if_not_found=False)
        for user in self:
            user.is_waiter = waiter_group and waiter_group in user.group_ids if waiter_group else False

    def _search_is_waiter(self, operator, value):
        waiter_group = self.env.ref('waiter_screen.group_waiter', raise_if_not_found=False)
        if waiter_group:
            if (operator == '=' and value) or (operator == '!=' and not value):
                return [('group_ids', 'in', [waiter_group.id])]
            else:
                return [('group_ids', 'not in', [waiter_group.id])]
        return [(0, '=', 1)]  # Return no users if group doesn't exist

    @api.model
    def waiter_authenticate(self, login, pin):
        """
        Authenticate waiter using login name and PIN
        Used by waiter screen login
        """
        if not login or not pin:
            raise UserError(_('Please enter both name and PIN'))

        # Find user by login or name
        user = self.search([
            '|',
            ('login', '=', login),
            ('name', 'ilike', login)
        ], limit=1)

        if not user:
            raise AccessDenied(_('Invalid waiter name'))

        # Check if user is a waiter
        if not user.is_waiter:
            raise AccessDenied(_('This user is not registered as a waiter'))

        # Verify PIN
        if user.waiter_pin != pin:
            raise AccessDenied(_('Invalid PIN'))

        # Get active session
        session_data = self.env['pos.session'].sudo().get_active_session_for_waiter()

        # Register waiter login
        session = self.env['pos.session'].sudo().browse(session_data['id'])
        session.waiter_login(user.id)

        return {
            'success': True,
            'user_id': user.id,  # Return user ID for session authentication
            'waiter': {
                'id': user.id,
                'name': user.name,
                'login': user.login,
                'employee_number': user.waiter_employee_number,
            },
            'session': session_data,
        }

    @api.model
    def get_waiter_statistics(self, waiter_id=None, date_from=None, date_to=None):
        """
        Get performance statistics for waiter
        Used in waiter dashboard
        """
        waiter_id = waiter_id or self.env.user.id

        domain = [
            ('waiter_id', '=', waiter_id),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]

        if date_from:
            domain.append(('date_order', '>=', date_from))
        if date_to:
            domain.append(('date_order', '<=', date_to))

        orders = self.env['pos.order'].search(domain)

        return {
            'total_orders': len(orders),
            'total_sales': sum(orders.mapped('amount_total')),
            'average_order_value': sum(orders.mapped('amount_total')) / len(orders) if orders else 0,
            'tables_served': len(orders.mapped('table_id')),
        }
