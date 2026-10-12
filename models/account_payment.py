# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, _, api

FEE_METHOD_CODES = {"card_charge_fees", "ach_charge_fees"}
FEE_LABEL_MAP = {
    "card_charge_fees": lambda _: _("Card Processing Fees"),
    "ach_charge_fees":  lambda _: _("ACH Processing Fees"),
}


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # Change in move lines to post Charge fees into the journal fee account.
    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        line_vals_list = super()._prepare_move_line_default_vals(
            write_off_line_vals, force_balance
        )
        code = self.payment_method_line_id.code
        if code not in FEE_METHOD_CODES:
            return line_vals_list

        fee_account = self.journal_id.default_account_id
        label = FEE_LABEL_MAP[code](_)

        if fee_account:
            for line in line_vals_list:
                if line.get("account_id") != self.outstanding_account_id.id:
                    line["account_id"] = fee_account.id
                    line["name"] = label

        return line_vals_list

    def _seek_for_lines(self):
        liquidity_lines, counterpart_lines, writeoff_lines = super()._seek_for_lines()
        # if (
        #     not counterpart_lines
        #     and self.payment_method_line_id.code in FEE_METHOD_CODES
        # ):
        if self.payment_method_line_id.code in FEE_METHOD_CODES:
            fee_account = self.journal_id.default_account_id
            # counterpart_lines = self.move_id.line_ids.filtered(
            #     lambda l: l.account_id == fee_account
            # )
            if fee_account:
                fee_counterpart = self.move_id.line_ids.filtered(
                    lambda l: l.account_id == fee_account
                )
                if fee_counterpart:
                    liquidity_lines = liquidity_lines.filtered(lambda l: l.id not in fee_counterpart.ids)
                    counterpart_lines = fee_counterpart
        return liquidity_lines, counterpart_lines, writeoff_lines
