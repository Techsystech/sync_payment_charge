# -*- coding: utf-8 -*-
{
    "name": "Payment Charge",
    "version": "18.0.1.0.0",
    "summary": "Payment Fees Charge",
    'sequence': 10,
    "description": """
Payment Fees Charge
    """,
    "category": "Accounting/Payment Providers",
    "author": "Synconics Technologies Pvt. Ltd.",
    "website": "https://www.synconics.com",
    "depends": [
        "base", "payment"
    ],
    "data": [
        "views/payment_provider_view.xml",
        "views/payment_transaction_view.xml",
        "views/payment_template.xml",
    ],
    'demo': [],
    'images': [
        'static/description/main_screen.png'
    ],
    'price': 45.0,
    'currency': 'EUR',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}
