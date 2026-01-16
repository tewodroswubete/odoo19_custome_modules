# Waiter Screen for Odoo 19 Restaurant

## Overview

The **Waiter Screen** module provides a dedicated, simplified interface for restaurant waiters to take orders and process payments without requiring full POS session access. Multiple waiters can work simultaneously on the same POS session opened by a manager.

## Features

✅ **Separate Waiter Interface** - Accessed via `/pos/waiter`
✅ **Multi-Waiter Support** - Multiple waiters can work simultaneously
✅ **PIN Authentication** - Quick and secure waiter login with 4-digit PIN
✅ **Table Management** - Visual floor plan with color-coded table statuses
✅ **Order Taking** - Self-ordering style product selection
✅ **Kitchen Integration** - Orders automatically sent to kitchen display
✅ **Real-time Notifications** - Waiters receive alerts when orders are ready
✅ **Payment Processing** - Accept cash, card, and other payment methods
✅ **Mobile-Friendly** - Responsive design optimized for tablets

## Installation

1. **Copy the module** to your Odoo addons directory:
   ```bash
   cp -r waiter_screen /opt/odoo19/custom_addons/
   ```

2. **Update apps list** in Odoo:
   - Go to Apps → Update Apps List
   - Search for "Waiter Screen"
   - Click Install

3. **Dependencies**: This module requires:
   - `point_of_sale` (Odoo standard)
   - `pos_restaurant` (Odoo standard)
   - `pos_enterprise` (Odoo enterprise)

## Configuration

### 1. Enable Waiter Screen in POS Config

1. Go to **Point of Sale → Configuration → Point of Sale**
2. Open your restaurant POS config
3. Scroll to **Waiter Screen** section
4. Enable "Enable Waiter Screen"
5. Copy the **Waiter Screen URL** to share with waiters

### 2. Create Waiter Users

1. Go to **Point of Sale → Configuration → Waiters**
2. Click **Create**
3. Fill in:
   - Name: Waiter's full name
   - Login: Username for waiter
   - **Waiter PIN**: 4-digit PIN (e.g., 1234)
   - Employee Number: (optional)
4. In the **Access Rights** tab:
   - Add group: **Waiter Screen / Waiter**
5. Save

### 3. Manager Opens POS Session

The manager must open a POS session before waiters can start:

1. Go to **Point of Sale → Dashboard**
2. Click **New Session**
3. Session is now active for waiters

## Usage Workflow

### Waiter Login

1. Waiter opens browser and goes to: `http://your-odoo-server.com/pos/waiter`
2. Enters their name
3. Enters 4-digit PIN using the PIN pad
4. Clicks **Login**

### Taking Orders

1. **Select Table**:
   - Waiter sees all tables on the floor plan
   - Color codes:
     - 🟢 Green = Available
     - 🔴 Red = Occupied
     - 🟡 Orange = Food preparing
     - 🔵 Blue = Ready to serve
   - Click on a table to start taking order

2. **Add Products**:
   - Browse products by category
   - Use search to find items quickly
   - Click product to add to order
   - Adjust quantities with +/- buttons
   - Add special instructions in notes field

3. **Send to Kitchen**:
   - Review order summary
   - Click **"Send to Kitchen"** button
   - Order is created and sent to kitchen display
   - Waiter receives notification when order is ready

### Processing Payment

1. After food is served, click the table again
2. Click **Payment** button
3. Select payment method (Cash, Card, Telebirr, etc.)
4. Enter amount received
5. Use quick amount buttons for common denominations
6. See change calculated automatically
7. Click **Complete Payment**
8. Table is marked as available

### Kitchen Notifications

When the kitchen marks an order as ready:
- Waiter receives a real-time notification
- Notification shows table number and order name
- Table status changes to "Ready" (blue)
- Waiter can then serve the food and collect payment

## Technical Architecture

```
┌─────────────────────┐
│  Manager Terminal   │
│  (Opens POS Session)│
└──────────┬──────────┘
           │
           ├──────────────────────────────────┐
           │                                  │
┌──────────▼──────────┐          ┌───────────▼────────────┐
│  WAITER SCREENS     │◄────────►│  KITCHEN DISPLAY       │
│  (Multiple Devices) │          │  (Preparation Display) │
│  - Waiter 1         │          └────────────────────────┘
│  - Waiter 2         │
│  - Waiter 3         │
└─────────────────────┘
```

## Data Flow

1. **Order Creation**:
   ```
   Waiter Screen → Select Table
                 → Add Products
                 → Send to Kitchen
                 → RPC: pos.order.create_from_waiter_ui()
                 → Order saved with waiter_id
                 → Kitchen display updates
   ```

2. **Kitchen Ready Notification**:
   ```
   Kitchen Display → Mark as Ready
                   → Bus notification sent
                   → Waiter receives alert
   ```

3. **Payment**:
   ```
   Waiter Screen → Enter amount
                 → Select payment method
                 → RPC: process_payment_from_waiter()
                 → Order marked as paid
                 → Table freed
   ```

## Permissions

The **Waiter** user group has the following permissions:

**CAN DO:**
- ✅ View and create POS orders
- ✅ View tables and floors
- ✅ View products and prices
- ✅ Create payments
- ✅ View active POS sessions

**CANNOT DO:**
- ❌ Open/close POS sessions
- ❌ Modify POS configuration
- ❌ Delete orders
- ❌ Access backend Odoo interface (limited access)
- ❌ View other waiters' orders

## Security Features

- **PIN Authentication**: 4-digit PIN for quick login
- **Data Isolation**: Waiters can only see their own orders
- **Read-only Access**: Products, tables, and configs are read-only
- **Session Validation**: Checks for active POS session before allowing login

## Customization

### Changing Colors

Edit `/static/src/scss/waiter_screen.scss`:

```scss
:root {
    --primary-color: #667eea;  /* Main brand color */
    --secondary-color: #764ba2; /* Secondary color */
    --success-color: #48bb78;   /* Available tables */
    --danger-color: #f56565;    /* Occupied tables */
    --warning-color: #ed8936;   /* Preparing status */
}
```

### Adding Custom Payment Methods

1. Go to **Point of Sale → Configuration → Payment Methods**
2. Create new payment method (e.g., "Mobile Money")
3. It will automatically appear in waiter payment screen

## Troubleshooting

### "No Active POS Session" Error

**Problem**: Waiter sees error when trying to login
**Solution**: Manager needs to open a POS session first

### Waiter Can't Login

**Problem**: Invalid name or PIN
**Solution**:
- Check waiter user has "Waiter" group
- Verify PIN is exactly 4 digits
- Try using login username instead of full name

### Kitchen Notifications Not Working

**Problem**: Waiter doesn't receive order ready notifications
**Solution**:
- Ensure `bus` module is installed
- Check browser allows notifications
- Refresh waiter screen

### Products Not Showing

**Problem**: Product list is empty
**Solution**:
- Ensure products have "Available in POS" checked
- Assign products to POS categories
- Refresh waiter data

## Support

For issues or feature requests, please contact your Odoo administrator.

## License

LGPL-3

## Credits

- **Author**: Your Company
- **Version**: 1.0.0
- **Odoo Version**: 19.0
