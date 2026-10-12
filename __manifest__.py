{
    "name": "Payment Fee Base",
    "version": "19.0.1.3",
    "summary": "Technical base module for payment fee management in Odoo. Works only as a dependency and does not function independently | Search Keyword: Odoo Payment Fee Base, Payment Fee Framework Odoo, Odoo Payment Charge Engine, Payment Provider Dependency Module, Odoo Fee Calculation Core, Payment Gateway Fee Base, Odoo Technical Base Module, Accounting Fee Integration Odoo, Payment fees, fee calculation, accounting integration, journal entries, payment provider, Odoo backend, financial workflow, technical module, ERP payment framework, payment automation, fee management, core dependency module, Odoo accounting tools",
    "sequence": 10,
    "description": """
Payment Fees Charge
    """,
    "category": "Accounting/Payment Providers",
    "author": "Synconics Technologies Pvt. Ltd.",
    "website": "https://www.synconics.com",
    "depends": ["base", "payment", "account"],
    "data": [
        "data/account_payment_method_data.xml",
        "views/payment_provider_view.xml",
        "views/payment_transaction_view.xml",
        "views/payment_template.xml",
        "views/account_payment_views.xml",
    ],
    "demo": [],
    "images": ["static/description/main_screen.png"],
    "live_test_url": "https://www.synconics.com/demo-odoo-apps?utm_source=odoo&utm_medium=apps-store&utm_campaign=sync_payment_charge",
    "price": 51.0,
    "currency": "EUR",
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "OPL-1",
}
