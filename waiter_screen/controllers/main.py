# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.exceptions import UserError


class WaiterScreenController(http.Controller):

    @http.route(['/pos/waiter', '/waiter', '/waiter/screen'], type='http', auth='public', methods=['GET'], csrf=False, save_session=False)
    def waiter_screen(self, **kwargs):
        """
        Waiter screen interface - separate from main POS
        Public route - no authentication required   
        """
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("=== WAITER SCREEN ROUTE ACCESSED ===")
        _logger.info(f"Request headers: {dict(request.httprequest.headers)}")
        _logger.info(f"Session: {request.session}")

        try:
            # Render waiter screen
            response = request.render('waiter_screen.index', {
                'session_info': {
                    'user_id': False,
                    'user_name': False,
                }
            })
            _logger.info("Template rendered successfully")
            return response
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            _logger.error(f"Error rendering template: {error_trace}")
            return request.make_response(f"""
                <html>
                <head>
                    <title>Error Loading Waiter Screen</title>
                    <style>
                        body {{ font-family: Arial; padding: 40px; background: #f5f5f5; }}
                        .error {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        h1 {{ color: #e74c3c; }}
                        pre {{ background: #2d2d2d; color: #f8f8f2; padding: 20px; border-radius: 5px; overflow: auto; }}
                    </style>
                </head>
                <body>
                    <div class="error">
                        <h1>⚠️ Error Loading Waiter Screen</h1>
                        <p><strong>Error:</strong> {str(e)}</p>
                        <h3>Traceback:</h3>
                        <pre>{error_trace}</pre>
                    </div>
                </body>
                </html>
            """, headers=[('Content-Type', 'text/html')])

    @http.route('/pos/waiter/data', type='json', auth='public', csrf=False)
    def get_waiter_data(self):
        """
        Get all data needed for waiter screen
        Called when waiter screen loads
        """
        # Check if waiter is authenticated via custom session
        waiter_id = request.session.get('waiter_id')
        if not waiter_id:
            return {'error': 'Not authenticated'}

        user = request.env['res.users'].sudo().browse(waiter_id)
        if not user.exists() or not user.has_group('waiter_screen.group_waiter'):
            return {'error': 'Access denied'}

        try:
            data = request.env['pos.session'].sudo().get_waiter_session_data()
            return data
        except Exception as e:
            import traceback
            return {'error': str(e), 'traceback': traceback.format_exc()}

    @http.route('/pos/waiter/login', type='json', auth='none', csrf=False)
    def waiter_login(self, login, pin):
        """
        Authenticate waiter using PIN and create Odoo session
        """
        try:
            # Authenticate waiter and get initial data
            result = request.env['res.users'].sudo().waiter_authenticate(login, pin)

            if result.get('success') and result.get('user_id'):
                # Store waiter info in session (custom key for waiter authentication)
                request.session['waiter_id'] = result['user_id']
                request.session['waiter_login'] = result['waiter']['login']

                # Get complete waiter data (tables, products, etc.)
                waiter_data = request.env['pos.session'].sudo().get_waiter_session_data()
                result.update(waiter_data)

            return result
        except Exception as e:
            import traceback
            return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}

    @http.route('/pos/waiter/create_order', type='json', auth='public', csrf=False)
    def create_order(self, table_id, lines, notes=''):
        """
        Create a new POS order from waiter screen
        """
        try:
            # Check if waiter is authenticated via custom session
            waiter_id = request.session.get('waiter_id')
            if not waiter_id:
                return {'success': False, 'error': 'Not authenticated. Please login again.'}

            # Check waiter group
            user = request.env['res.users'].sudo().browse(waiter_id)
            if not user.exists() or not user.has_group('waiter_screen.group_waiter'):
                return {'success': False, 'error': 'Access denied - not a waiter'}

            # Get active session
            session = request.env['pos.session'].sudo().get_active_session_for_waiter()
            session_obj = request.env['pos.session'].sudo().browse(session['id'])

            # Calculate totals
            subtotal = sum(line['qty'] * line['price_unit'] for line in lines)

            # Create the order with all required fields
            order_vals = {
                'session_id': session_obj.id,
                'config_id': session_obj.config_id.id,
                'table_id': table_id,
                'user_id': waiter_id,
                'amount_tax': 0.0,  # Required field
                'amount_total': subtotal,
                'amount_paid': 0.0,
                'amount_return': 0.0,
                'lines': [(0, 0, {
                    'product_id': line['product_id'],
                    'qty': line['qty'],
                    'price_unit': line['price_unit'],
                    'full_product_name': line['product_name'],
                    'price_subtotal': line['qty'] * line['price_unit'],
                    'price_subtotal_incl': line['qty'] * line['price_unit'],
                }) for line in lines],
            }

            # Add waiter_id if the field exists (custom field from our module)
            if 'waiter_id' in request.env['pos.order']._fields:
                order_vals['waiter_id'] = waiter_id

            order = request.env['pos.order'].sudo().create(order_vals)

            # Update table to mark as occupied with this order
            table = request.env['restaurant.table'].sudo().browse(table_id)
            table.write({'current_order_id': order.id})

            return {
                'success': True,
                'order_id': order.id,
                'order_name': order.name,
                'amount_total': order.amount_total,
            }

        except Exception as e:
            import traceback
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error("Failed to create order: %s", traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    @http.route('/pos/waiter/add_items_to_order', type='json', auth='public', csrf=False)
    def add_items_to_order(self, order_id, lines):
        """
        Add additional items to an existing order
        """
        try:
            waiter_id = request.session.get('waiter_id')
            if not waiter_id:
                return {'success': False, 'error': 'Not authenticated'}

            # Get the existing order
            order = request.env['pos.order'].sudo().browse(order_id)

            if not order.exists():
                return {'success': False, 'error': 'Order not found'}

            # Add new lines to the order
            new_lines = []
            for line in lines:
                # Check if this is a new line (no id) or existing line (has id)
                if not line.get('id'):
                    # New line - create it
                    new_lines.append((0, 0, {
                        'product_id': line['product_id'],
                        'qty': line['qty'],
                        'price_unit': line['price_unit'],
                        'full_product_name': line['product_name'],
                        'price_subtotal': line['qty'] * line['price_unit'],
                        'price_subtotal_incl': line['qty'] * line['price_unit'],
                    }))
                else:
                    # Existing line - update quantity
                    new_lines.append((1, line['id'], {
                        'qty': line['qty'],
                        'price_subtotal': line['qty'] * line['price_unit'],
                        'price_subtotal_incl': line['qty'] * line['price_unit'],
                    }))

            # Update the order with new lines
            order.write({'lines': new_lines})

            # Recalculate totals
            order._compute_amount_all()

            return {
                'success': True,
                'order_id': order.id,
                'order_name': order.name,
                'amount_total': order.amount_total,
            }

        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    @http.route('/pos/waiter/get_table_order', type='json', auth='public', csrf=False)
    def get_table_order(self, table_id):
        """
        Get existing order for a table (for occupied tables)
        """
        try:
            waiter_id = request.session.get('waiter_id')
            if not waiter_id:
                return {'success': False, 'error': 'Not authenticated'}

            # Get table and its current order
            table = request.env['restaurant.table'].sudo().browse(table_id)

            if not table.exists():
                return {'success': False, 'error': 'Table not found'}

            if not table.current_order_id:
                return {'success': False, 'error': 'No active order for this table'}

            order = table.current_order_id

            # Get order lines
            lines = []
            for line in order.lines:
                lines.append({
                    'id': line.id,
                    'product_id': line.product_id.id,
                    'product_name': line.full_product_name or line.product_id.name,
                    'qty': line.qty,
                    'price_unit': line.price_unit,
                    'price_subtotal': line.price_subtotal,
                })

            return {
                'success': True,
                'order': {
                    'id': order.id,
                    'name': order.name,
                    'table_id': order.table_id.id,
                    'amount_total': order.amount_total,
                    'amount_tax': order.amount_tax,
                    'state': order.state,
                    'lines': lines,
                },
            }

        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    @http.route('/pos/waiter/process_payment', type='json', auth='public', csrf=False)
    def process_payment(self, order_id, payment_method_id, amount):
        """
        Process payment for an order
        """
        try:
            waiter_id = request.session.get('waiter_id')
            if not waiter_id:
                return {'success': False, 'error': 'Not authenticated'}

            # Get the order
            order = request.env['pos.order'].sudo().browse(order_id)

            if not order.exists():
                return {'success': False, 'error': 'Order not found'}

            # Create payment
            payment_vals = {
                'pos_order_id': order.id,
                'amount': amount,
                'payment_method_id': payment_method_id,
                'session_id': order.session_id.id,
            }

            payment = request.env['pos.payment'].sudo().create(payment_vals)

            # Mark order as paid
            order.write({
                'amount_paid': amount,
                'state': 'paid',
            })

            # Free up the table
            if order.table_id:
                order.table_id.write({'current_order_id': False})

            return {
                'success': True,
                'payment_id': payment.id,
                'order_name': order.name,
            }

        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    @http.route('/pos/waiter/logout', type='json', auth='public', csrf=False)
    def waiter_logout(self):
        """
        Logout waiter from current session
        """
        try:
            waiter_id = request.session.get('waiter_id')
            if not waiter_id:
                return {'success': False, 'error': 'Not authenticated'}

            session = request.env['pos.session'].sudo().get_active_session_for_waiter()
            session_obj = request.env['pos.session'].sudo().browse(session['id'])
            session_obj.waiter_logout(waiter_id)

            # Clear waiter session
            request.session.pop('waiter_id', None)
            request.session.pop('waiter_login', None)

            return {'success': True}
        except Exception as e:
            import traceback
            return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}
