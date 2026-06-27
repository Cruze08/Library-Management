# library_management/library_management/doctype/library_fine/library_fine.py
import frappe
from frappe.model.document import Document
from frappe.utils import flt


class LibraryFine(Document):

    # ─── Before Save ─────────────────────────────────────────────

    def before_save(self):
        self._calculate_outstanding()

    def validate(self):
        self._calculate_outstanding()
        self._validate_waiver()

    def _calculate_outstanding(self):
        waiver = flt(self.waiver_amount)
        paid   = flt(self.paid_amount)
        total  = flt(self.total_fine)
        self.outstanding_amount = max(total - paid - waiver, 0)

    def _validate_waiver(self):
        if flt(self.waiver_amount) > 0 and not self.waiver_reason:
            frappe.throw("Please enter a <b>Waiver Reason</b> before saving.")
        if flt(self.waiver_amount) > flt(self.total_fine):
            frappe.throw("Waiver Amount cannot exceed Total Fine.")

    # ─── On Submit — post GL entry ────────────────────────────────

    def on_submit(self):
        self._post_fine_gl_entry()
        self._update_status()
        self._update_member_outstanding()

    def on_cancel(self):
        self._cancel_gl_entry()
        self._update_member_outstanding()

    # ─── GL Entry: Dr. Fine Receivable / Cr. Fine Income ─────────

    def _post_fine_gl_entry(self):
        settings = frappe.get_single("Library Settings")

        if not settings.fine_income_account:
            frappe.msgprint(
                "Fine Income Account not set in Library Settings. "
                "GL entry skipped.",
                alert=True
            )
            return

        if not settings.receivable_account:
            frappe.msgprint(
                "Fine Receivable Account not set in Library Settings. "
                "GL entry skipped.",
                alert=True
            )
            return

        member_doc = frappe.get_doc("Library Member", self.member)
        party = member_doc.customer  # ERPNext Customer linked to member

        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "posting_date": frappe.utils.today(),
            "company": frappe.defaults.get_user_default("Company"),
            "user_remark": f"Library fine for {self.member} — {self.book_issue}",
            "accounts": [
                {
                    # Debit: Fine Receivable
                    "account": settings.receivable_account,
                    "debit_in_account_currency": flt(self.total_fine),
                    "credit_in_account_currency": 0,
                    "party_type": "Customer",
                    "party": party,
                    "reference_type": "Library Fine",
                    "reference_name": self.name,
                },
                {
                    # Credit: Fine Income
                    "account": settings.fine_income_account,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": flt(self.total_fine),
                    "reference_type": "Library Fine",
                    "reference_name": self.name,
                }
            ]
        })
        je.insert(ignore_permissions=True)
        je.submit()

        self.db_set("journal_entry", je.name)
        frappe.msgprint(
            f"GL Entry <b>{je.name}</b> posted — "
            f"Dr. Fine Receivable / Cr. Fine Income ₹{self.total_fine}",
            alert=True
        )

    def _cancel_gl_entry(self):
        if self.journal_entry and frappe.db.exists("Journal Entry", self.journal_entry):
            je = frappe.get_doc("Journal Entry", self.journal_entry)
            if je.docstatus == 1:
                je.cancel()
            self.db_set("journal_entry", None)

    # ─── Payment recording ────────────────────────────────────────

    @frappe.whitelist()
    def record_payment(self, amount, payment_account=None):
        """
        Record a (partial or full) fine payment.
        Posts a GL entry: Dr. Cash/Bank / Cr. Fine Receivable
        """
        amount = flt(amount)
        if amount <= 0:
            frappe.throw("Payment amount must be greater than zero.")

        if amount > flt(self.outstanding_amount):
            frappe.throw(
                f"Payment ₹{amount} exceeds outstanding amount "
                f"₹{self.outstanding_amount}."
            )

        # Update paid amount
        self.paid_amount = flt(self.paid_amount) + amount
        self._calculate_outstanding()
        self._update_status()
        self.save(ignore_permissions=True)

        # Post payment GL entry
        self._post_payment_gl_entry(amount, payment_account)

        # Update member outstanding balance
        self._update_member_outstanding()

        frappe.msgprint(
            f"Payment of ₹{amount} recorded. "
            f"Outstanding: ₹{self.outstanding_amount}",
            alert=True
        )

    def _post_payment_gl_entry(self, amount, payment_account=None):
        settings = frappe.get_single("Library Settings")
        company  = frappe.defaults.get_user_default("Company")

        # Use passed account or fall back to default cash account
        if not payment_account:
            payment_account = frappe.db.get_value(
                "Account",
                {"account_type": "Cash", "company": company},
                "name"
            )

        if not payment_account or not settings.receivable_account:
            frappe.msgprint(
                "Payment account or Receivable account missing. "
                "GL entry skipped.",
                alert=True
            )
            return

        member_doc  = frappe.get_doc("Library Member", self.member)
        party       = member_doc.customer

        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Cash Entry",
            "posting_date": frappe.utils.today(),
            "company": company,
            "user_remark": f"Fine payment by {self.member} for {self.name}",
            "accounts": [
                {
                    # Debit: Cash / Bank
                    "account": payment_account,
                    "debit_in_account_currency": amount,
                    "credit_in_account_currency": 0,
                    "reference_type": "Library Fine",
                    "reference_name": self.name,
                },
                {
                    # Credit: Fine Receivable
                    "account": settings.receivable_account,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": amount,
                    "party_type": "Customer",
                    "party": party,
                    "reference_type": "Library Fine",
                    "reference_name": self.name,
                }
            ]
        })
        je.insert(ignore_permissions=True)
        je.submit()
        frappe.msgprint(
            f"Payment GL Entry <b>{je.name}</b> posted — "
            f"Dr. Cash / Cr. Fine Receivable ₹{amount}",
            alert=True
        )

    # ─── Waiver ───────────────────────────────────────────────────

    @frappe.whitelist()
    def apply_waiver(self, waiver_amount, reason):
        """Authorized staff can waive part or all of a fine."""
        self.waiver_amount = flt(waiver_amount)
        self.waiver_reason = reason
        self._calculate_outstanding()
        self._update_status()
        self.save(ignore_permissions=True)
        self._update_member_outstanding()
        frappe.msgprint(
            f"Waiver of ₹{waiver_amount} applied. Reason: {reason}",
            alert=True
        )

    # ─── Status + member rollup ───────────────────────────────────

    def _update_status(self):
        outstanding = flt(self.outstanding_amount)
        paid        = flt(self.paid_amount)
        waiver      = flt(self.waiver_amount)

        if waiver >= flt(self.total_fine):
            self.status = "Waived"
        elif outstanding <= 0:
            self.status = "Paid"
        elif paid > 0:
            self.status = "Partially Paid"
        else:
            self.status = "Unpaid"

    def _update_member_outstanding(self):
        member = frappe.get_doc("Library Member", self.member)
        member.update_outstanding_fine()