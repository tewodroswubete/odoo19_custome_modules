# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RestaurantTable(models.Model):
    _inherit = 'restaurant.table'

    current_order_id = fields.Many2one(
        'pos.order',
        string='Current Order',
        help='The active order for this table',
    )

    table_status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('preparing', 'Food Preparing'),
        ('ready', 'Ready to Serve'),
        ('payment', 'Awaiting Payment'),
    ], string='Status', compute='_compute_table_status', store=False)

    current_waiter_id = fields.Many2one(
        'res.users',
        related='current_order_id.waiter_id',
        string='Current Waiter',
        store=False,
    )

    @api.depends('current_order_id', 'current_order_id.state', 'current_order_id.kitchen_status')
    def _compute_table_status(self):
        for table in self:
            if not table.current_order_id or table.current_order_id.state in ['paid', 'done', 'invoiced']:
                table.table_status = 'available'
            elif table.current_order_id.kitchen_status == 'ready':
                table.table_status = 'ready'
            elif table.current_order_id.kitchen_status in ['sent', 'preparing']:
                table.table_status = 'preparing'
            elif table.current_order_id.state == 'draft':
                table.table_status = 'occupied'
            else:
                table.table_status = 'occupied'

    @api.model
    def get_tables_status(self, floor_ids=None):
        """
        Get real-time status of all tables for waiter screen
        """
        domain = [('active', '=', True)]
        if floor_ids:
            domain.append(('floor_id', 'in', floor_ids))

        tables = self.search(domain)

        result = []
        for table in tables:
            result.append({
                'id': table.id,
                'table_number': table.table_number,
                'floor_id': table.floor_id.id,
                'floor_name': table.floor_id.name,
                'seats': table.seats,
                'status': table.table_status,
                'current_order_id': table.current_order_id.id if table.current_order_id else False,
                'current_waiter_id': table.current_waiter_id.id if table.current_waiter_id else False,
                'current_waiter_name': table.current_waiter_id.name if table.current_waiter_id else False,
                'position_h': table.position_h,
                'position_v': table.position_v,
                'width': table.width,
                'height': table.height,
                'shape': table.shape,
                'color': table.color,
            })

        return result
