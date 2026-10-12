# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, api, fields

FEE_METHOD_CODES = {"card_charge_fees", "ach_charge_fees"}


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        for code in FEE_METHOD_CODES:
            res[code] = {
                "mode": "multi",
                "domain": [("type", "=", "general")],
            }
        return res

class PaymentMethodLine(models.Model):
    _inherit = "account.payment.method.line"

    card_fee_journal_id = fields.Many2one(
        comodel_name="account.journal",
        ondelete="cascade",
        check_company=True,
    )
    ach_fee_journal_id = fields.Many2one(
        comodel_name="account.journal",
        ondelete="cascade",
        check_company=True,
    )


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def write(self, vals):
        res = super().write(vals)

        if "default_account_id" not in vals:
            return res

        new_account_id = vals.get("default_account_id")

        all_providers = self.env["payment.provider"].search(
            [("code", "in", ("stripe", "authorize"))]
        )
        for journal in self:
            for provider in all_providers:
                vals_to_write = {}
                if provider.card_fees_journal_id == journal:
                    vals_to_write["card_fees_account_id"] = new_account_id
                if provider.ach_fees_journal_id == journal:
                    vals_to_write["ach_fees_account_id"] = new_account_id

                if vals_to_write:
                    provider.with_context(_skip_fee_account_sync=True).write(
                        vals_to_write
                    )

        return res