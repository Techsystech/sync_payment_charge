# -*- coding: utf-8 -*-

from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    support_fees = fields.Boolean(
        string="Fees Supported", compute="_compute_feature_support_fields"
    )

    def _compute_feature_support_fields(self):
        """
        Override of `payment` to enable additional features.
        """
        super()._compute_feature_support_fields()
        self.support_fees = False

    def compute_fees(self, pm_sudo, amount, **kwargs):
        """
        New method which will calculate fees
        """
        self.ensure_one()
        return amount

    def is_support_fees(self, method):
        """
        New method for method support fees
        """
        self.ensure_one()
        return False
