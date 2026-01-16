# -*- coding: utf-8 -*-
{
    'name': 'Waiter Screen for Restaurant',
    'version': '1.0.0',
    'category': 'Sales/Point of Sale',
    'sequence': 10,
    'author': 'teddy',
    'summary': 'Dedicated waiter interface for taking orders and payments without POS session access',
    'description': """
        Waiter Screen Module
        ====================
        - Separate interface for waiters (not full POS access)
        - Multiple waiters can work simultaneously
        - Connected to one active POS session opened by manager
        - Table management and order taking
        - Kitchen display integration with notifications
        - Payment processing through waiter screen
        - Similar to self-ordering and kitchen display workflow

        Workflow:
        ---------
        1. Manager opens POS session
        2. Waiters login to /pos/waiter
        3. Select table → Order food → Send to kitchen
        4. Kitchen prepares → Notifies waiter when ready
        5. Waiter receives payment → Order completed
    """,
    'depends': [
        'point_of_sale',
        'pos_restaurant',
        'pos_enterprise',
    ],
    'data': [
        'security/waiter_security.xml',
        'security/ir.model.access.csv',
        'views/waiter_assets_index.xml',
        'views/pos_config_views.xml',
        'views/waiter_user_views.xml',
        'data/waiter_data.xml',
    ],
    'assets': {
        # Waiter screen assets - use web frontend base
        'waiter_screen.assets': [
            # Use web frontend assets (lighter than backend)
            ('include', 'web.assets_frontend'),

            # Waiter screen specific files
            'waiter_screen/static/src/app/**/*.js',
            'waiter_screen/static/src/app/**/*.xml',
            'waiter_screen/static/src/scss/**/*.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'author': 'Your Company',
}
