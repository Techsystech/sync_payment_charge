# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    fees = fields.Monetary(
        string="Fees",
        currency_field="currency_id",
        help="The fees amount; set by the system as it depends on the provider",
        readonly=True,
    )

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if not (self.provider_code in ['stripe', 'authorize']):
            return res
        if self.fees:
            total_fee = self.currency_id.round(self.amount + self.fees)
        else:
            total_fee = self.amount
        rendering_values = {
            "total_fee": f"{total_fee:.2f}",
            "handling": self.fees,
        }
        return rendering_values

    # === CRUD METHODS ===#
    @api.model_create_multi
    def create(self, values_list):
        """
        Inherit create method which add fees if the provider have support fees
        """
        for values in values_list:
            provider = self.env["payment.provider"].browse(values["provider_id"])
            method = self.env["payment.method"].browse(values.get("payment_method_id"))
            partner = self.env["res.partner"].browse(values["partner_id"])
            amount = values.get("amount", 0)
            values["fees"] = 0
            if (
                provider.is_support_fees(method)
                and values.get("operation") not in ["validation", "refund"]
            ):
                currency = (
                    self.env["res.currency"].browse(values.get("currency_id")).exists()
                )
                values["fees"] = provider.compute_fees(
                    method, amount, currency=currency, partner_id=partner.id
                )
        txs = super().create(values_list)
        txs.invalidate_recordset(["amount", "fees"])
        return txs
