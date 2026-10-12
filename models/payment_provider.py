# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import fields, models, api


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    support_fees = fields.Boolean(
        string="Fees Supported", compute="_compute_feature_support_fields"
    )

    # Card
    card_fees_journal_id = fields.Many2one(
        "account.journal",
        string="Card Fee Journal",
        help="Journal to post payment provider transaction fees.",
        domain=[("type", "=", "general")],
        compute="_compute_card_fee_journal_id",
        inverse="_inverse_card_fee_journal_id",
        check_company=True,
        copy=False,
        required=True,
    )
    card_fees_account_id = fields.Many2one(
        "account.account",
        string="Card Fee Credit Account",
        # domain="[('account_type', '!=', 'asset_cash')]",
        domain="[('account_type', '=', 'asset_receivable')]",
        check_company=True,
        copy=False,
        required=True,
    )

    # ACH
    ach_fees_journal_id = fields.Many2one(
        "account.journal",
        string="ACH Fee Journal",
        help="Journal to post ACH transaction fees.",
        domain=[("type", "=", "general")],
        compute="_compute_ach_fee_journal_id",
        inverse="_inverse_ach_fee_journal_id",
        check_company=True,
        copy=False,
        required=True,
    )
    ach_fees_account_id = fields.Many2one(
        "account.account",
        string="ACH Fee Credit Account",
        domain="[('account_type', '=', 'asset_receivable')]",
        check_company=True,
        copy=False,
        required=True,
    )


    @api.onchange("card_fees_journal_id")
    def _onchange_card_fees_journal_id(self):
        for rec in self:
            rec.card_fees_account_id = rec.card_fees_journal_id.default_account_id or False

    @api.onchange("ach_fees_journal_id")
    def _onchange_ach_fees_journal_id(self):
        for rec in self:
            rec.ach_fees_account_id = rec.ach_fees_journal_id.default_account_id or False

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record, vals in zip(res, vals_list):
            record._sync_fee_journal_accounts(vals)
        return res

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            record._sync_fee_journal_accounts(vals)
        return res

    def copy(self, default=None):
        """Override to ensure journals are not recomputed during duplication."""
        return super(
            PaymentProvider, self.with_context(skip_journal_compute=True)
        ).copy(default)

    def _sync_fee_journal_accounts(self, vals=None):
        self.ensure_one()
        if self.code not in ("stripe", "authorize") or self.env.context.get(
            "_skip_fee_account_sync"
        ):
            return
        if vals is None:
            vals = {}

        if "card_fees_account_id" in vals and self.card_fees_journal_id:
            self.card_fees_journal_id.with_context(_skip_fee_account_sync=True).write(
                {"default_account_id": self.card_fees_account_id.id}
            )
        elif "ach_fees_account_id" in vals and self.ach_fees_journal_id:
            self.ach_fees_journal_id.with_context(_skip_fee_account_sync=True).write(
                {"default_account_id": self.ach_fees_account_id.id}
            )

    # # ===Card COMPUTE / INVERSE METHODS === #

    def _ensure_payment_method_line_card_fees(self, allow_create=True):
        self.ensure_one()
        if not self.id:
            return
        # import pdb; pdb.set_trace()
        default_payment_method = self._get_provider_payment_method("card_charge_fees")
        if not default_payment_method:
            return

        pay_method_line = self.env["account.payment.method.line"].search(
            [
                ("code", "=", "card_charge_fees"),
                ("journal_id", "!=", False),
                ("journal_id.company_id", "=", self.company_id.id),
            ],
            limit=1,
        )

        if not self.card_fees_journal_id:
            if pay_method_line:
                pay_method_line.unlink()
                return

        if not pay_method_line:
            pay_method_line = self.env["account.payment.method.line"].search(
                [
                    *self.env["account.payment.method.line"]._check_company_domain(
                        self.company_id
                    ),
                    ("code", "=", "card_charge_fees"),
                    ("journal_id", "!=", False),
                    ("journal_id.company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
        if pay_method_line:
            pay_method_line.journal_id = self.card_fees_journal_id
            pay_method_line.name = "Card Charge Fees"
        elif allow_create:
            create_values = {
                "name": "Card Charge Fees",
                "payment_method_id": default_payment_method.id,
                "journal_id": self.card_fees_journal_id.id,
            }
            pay_method_line_same_code = self.env["account.payment.method.line"].search(
                [
                    *self.env["account.payment.method.line"]._check_company_domain(
                        self.company_id
                    ),
                    ("code", "=", "card_charge_fees"),
                ],
                limit=1,
            )
            if pay_method_line_same_code:
                create_values["payment_account_id"] = (
                    pay_method_line_same_code.payment_account_id.id
                )
            self.env["account.payment.method.line"].create(create_values)

    @api.depends("code", "state", "company_id")
    def _compute_card_fee_journal_id(self):
        if self.env.context.get("skip_journal_compute"):
            return
        for provider in self:
            pay_method_line = self.env["account.payment.method.line"].search(
                [
                    ("code", "=", "card_charge_fees"),
                    ("journal_id", "!=", False),
                    ("journal_id.company_id", "=", provider.company_id.id),
                ],
                limit=1,
            )
            # if pay_method_line:
            if pay_method_line and pay_method_line.journal_id.type == "general":
                provider.card_fees_journal_id = pay_method_line.journal_id
            elif provider.state in ("enabled", "test"):
                card_fees_journal_id = self.env["account.journal"].search(
                    [
                        ("company_id", "=", provider.company_id.id),
                        ("id", "!=", provider.journal_id.id),
                        ("type", "=", "general"),
                    ],
                    limit=1,
                )
                provider.card_fees_journal_id = card_fees_journal_id
                if provider.id:
                    provider._ensure_payment_method_line_card_fees()

    def _inverse_card_fee_journal_id(self):
        for provider in self:
            provider._ensure_payment_method_line_card_fees()

    # # ===ACH COMPUTE / INVERSE METHODS === #

    def _ensure_payment_method_line_ach_fees(self, allow_create=True):
        self.ensure_one()
        if not self.id:
            return
        # import pdb; pdb.set_trace()
        default_payment_method = self._get_provider_payment_method("ach_charge_fees")
        if not default_payment_method:
            return

        pay_method_line = self.env["account.payment.method.line"].search(
            [
                ("code", "=", "ach_charge_fees"),
                ("journal_id", "!=", False),
                ("journal_id.company_id", "=", self.company_id.id),
            ],
            limit=1,
        )

        if not self.ach_fees_journal_id:
            if pay_method_line:
                pay_method_line.unlink()
                return

        if not pay_method_line:
            pay_method_line = self.env["account.payment.method.line"].search(
                [
                    *self.env["account.payment.method.line"]._check_company_domain(
                        self.company_id
                    ),
                    ("code", "=", "ach_charge_fees"),
                    ("journal_id", "!=", False),
                    ("journal_id.company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
        if pay_method_line:
            pay_method_line.journal_id = self.ach_fees_journal_id
            pay_method_line.name = "ACH Charge Fees"
        elif allow_create:
            create_values = {
                "name": "ACH Charge Fees",
                "payment_method_id": default_payment_method.id,
                "journal_id": self.ach_fees_journal_id.id,
            }
            pay_method_line_same_code = self.env["account.payment.method.line"].search(
                [
                    *self.env["account.payment.method.line"]._check_company_domain(
                        self.company_id
                    ),
                    ("code", "=", "ach_charge_fees"),
                ],
                limit=1,
            )
            if pay_method_line_same_code:
                create_values["payment_account_id"] = (
                    pay_method_line_same_code.payment_account_id.id
                )
            self.env["account.payment.method.line"].create(create_values)

    @api.depends("code", "state", "company_id")
    def _compute_ach_fee_journal_id(self):
        if self.env.context.get("skip_journal_compute"):
            return
        for provider in self:
            pay_method_line = self.env["account.payment.method.line"].search(
                [
                    ("code", "=", "ach_charge_fees"),
                    ("journal_id", "!=", False),
                    ("journal_id.company_id", "=", provider.company_id.id),
                ],
                limit=1,
            )
            # if pay_method_line:
            if pay_method_line and pay_method_line.journal_id.type == "general":
                provider.ach_fees_journal_id = pay_method_line.journal_id
            elif provider.state in ("enabled", "test"):
                ach_fees_journal_id = self.env["account.journal"].search(
                    [
                        ("company_id", "=", provider.company_id.id),
                        ("id", "!=", provider.journal_id.id),
                        ("type", "=", "general"),
                    ],
                    limit=1,
                )
                provider.ach_fees_journal_id = ach_fees_journal_id
                if provider.id:
                    provider._ensure_payment_method_line_ach_fees()

    def _inverse_ach_fee_journal_id(self):
        for provider in self:
            provider._ensure_payment_method_line_ach_fees()

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
