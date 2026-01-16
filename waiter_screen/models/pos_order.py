# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    waiter_id = fields.Many2one(
        'res.users',
        string='Waiter',
        help='Waiter who took this order',
        index=True,
    )

    kitchen_status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent to Kitchen'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
    ], default='draft', string='Kitchen Status', tracking=True)

    waiter_notes = fields.Text(
        string='Waiter Notes',
        help='Special instructions from waiter (allergies, preferences, etc.)'
    )

    @api.model
    def create_from_waiter_ui(self, orders):
        """
        Create order from waiter screen
        Similar to create_from_ui but simplified for waiter workflow
        """
        order_ids = []
        for order in orders:
            # Add waiter info
            order['data']['waiter_id'] = self.env.user.id
            order['data']['kitchen_status'] = 'sent'

            # Use standard POS order creation
            order_id = self._process_order(order, draft=False)
            order_ids.append(order_id)

            # Notify kitchen display if preparation display is installed
            if order_id:
                pos_order = self.browse(order_id)
                self._notify_kitchen_new_order(pos_order)

        return order_ids

    def _notify_kitchen_new_order(self, order):
        """Send notification to kitchen display"""
        self.env['bus.bus']._sendone(
            f'preparation_display_{order.config_id.id}',
            'new_order',
            {
                'order_id': order.id,
                'order_name': order.name,
                'table': order.table_id.table_number if order.table_id else False,
                'floor': order.table_id.floor_id.name if order.table_id and order.table_id.floor_id else False,
            }
        )

    def mark_as_ready_from_kitchen(self):
        """
        Called by kitchen display when order is ready
        Notifies the waiter
        """
        self.ensure_one()
        self.kitchen_status = 'ready'

        # Send notification to waiter
        if self.waiter_id:
            self.env['bus.bus']._sendone(
                f'waiter_{self.waiter_id.id}',
                'order_ready',
                {
                    'order_id': self.id,
                    'order_name': self.name,
                    'table': self.table_id.table_number if self.table_id else False,
                    'floor': self.table_id.floor_id.name if self.table_id and self.table_id.floor_id else False,
                }
            )

        return True

    def mark_as_served(self):
        """Waiter marks order as served/delivered to customer"""
        self.ensure_one()
        self.kitchen_status = 'served'
        return True

    @api.model
    def process_payment_from_waiter(self, order_id, payment_data):
        """
        Process payment from waiter screen
        payment_data: {
            'amount': float,
            'payment_method_id': int,
            'payment_name': str,
        }
        """
        order = self.browse(order_id)
        if not order.exists():
            raise UserError(_('Order not found'))

        # Create payment
        payment_vals = {
            'pos_order_id': order.id,
            'amount': payment_data['amount'],
            'payment_method_id': payment_data['payment_method_id'],
            'name': payment_data.get('payment_name', 'Payment'),
            'session_id': order.session_id.id,
        }

        self.env['pos.payment'].create(payment_vals)

        # Mark order as paid if full amount received
        if order.amount_total <= payment_data['amount']:
            order.write({
                'state': 'paid',
                'kitchen_status': 'served',
            })

            # Free up the table
            if order.table_id:
                order.table_id.write({'current_order_id': False})

        return {
            'success': True,
            'order_id': order.id,
            'state': order.state,
        }

    @api.model
    def get_waiter_orders(self, session_id=None, waiter_id=None):
        """Get orders for waiter screen dashboard"""
        domain = []

        if session_id:
            domain.append(('session_id', '=', session_id))

        if waiter_id:
            domain.append(('waiter_id', '=', waiter_id))
        else:
            domain.append(('waiter_id', '=', self.env.user.id))

        # Only get today's orders
        domain.append(('date_order', '>=', fields.Datetime.now().replace(hour=0, minute=0, second=0)))

        orders = self.search(domain, order='date_order desc')

        return orders.read([
            'name', 'table_id', 'amount_total', 'state',
            'kitchen_status', 'date_order', 'waiter_id'
        ])
