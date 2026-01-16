{
    "name": "Payment Provider: Telebirr (inline)",
    "version": "19.0.1.0.0",
    "category": "Accounting/Payment Providers",
    "summary": "Inline Telebirr H5 payments for e‑Commerce, POS Self‑Order & Kiosk",
    "author": "Tewodros Wubete",
    "depends": [
        "payment",            # core payment framework
        "website_payment",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",

        # Views and Templates (must load before data that references them)
        "views/telebirr_templates.xml",
        "views/telebirr_assets.xml",
        "views/payment_views.xml",
        "views/telebirr_mapping_views.xml",

        # Data
        "data/payment_method_data.xml",
        "data/payment_provider_data.xml",
    ],
    "assets": {
        'web.assets_frontend': [
            'payment_telebirr/static/src/interactions/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    "license": "LGPL-3",
}