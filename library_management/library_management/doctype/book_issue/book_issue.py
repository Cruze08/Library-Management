# library_management/library_management/doctype/book_issue/book_issue.py
import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, date_diff, add_days


class BookIssue(Document):

    # ─── Validation ──────────────────────────────────────────────

    def validate(self):
        self._set_due_date()
        self._validate_availability()
        self._validate_membership()
        self._validate_return_date()

    def _set_due_date(self):
        if not self.due_date and self.issue_date:
            settings = frappe.get_single("Library Settings")
            loan_days = settings.loan_period_days or 14
            self.due_date = add_days(self.issue_date, loan_days)

    def _validate_availability(self):
        if self.is_new():
            book = frappe.get_doc("Book", self.book)
            if (book.available_copies or 0) < 1:
                frappe.throw(
                    f"No copies of <b>{book.title}</b> are available for issue."
                )

    def _validate_membership(self):
        from library_management.library_management.doctype.library_member.library_member import LibraryMember
        LibraryMember.validate_membership(self.member)

    def _validate_return_date(self):
        if self.return_date and self.issue_date:
            if getdate(self.return_date) < getdate(self.issue_date):
                frappe.throw("Return date cannot be before Issue date.")

    # ─── On Submit — issue the book ──────────────────────────────

    def on_submit(self):
        self.status = "Issued"
        book = frappe.get_doc("Book", self.book)
        book.decrement_available()
        frappe.msgprint(
            f"Book <b>{book.title}</b> issued to <b>{self.member}</b>. "
            f"Due by <b>{self.due_date}</b>.",
            alert=True
        )

    # ─── On Cancel — reverse the issue ───────────────────────────

    def on_cancel(self):
        if self.status == "Returned":
            frappe.throw(
                "This book has already been returned. Cannot cancel."
            )
        book = frappe.get_doc("Book", self.book)
        book.increment_available()
        self.status = "Cancelled"

    # ─── Return processing ────────────────────────────────────────

    @frappe.whitelist()
    def process_return(self):
        """Call from UI button or API to return a book and auto-raise fine."""
        if self.status == "Returned":
            frappe.throw("This book has already been returned.")

        self.return_date = today()
        overdue_days = date_diff(self.return_date, self.due_date)

        if overdue_days > 0:
            self.status = "Overdue"
            self._create_fine(overdue_days)
        else:
            self.status = "Returned"

        # Restore book copy
        book = frappe.get_doc("Book", self.book)
        book.increment_available()

        self.save(ignore_permissions=True)
        frappe.msgprint(
            f"Book returned successfully. "
            + (f"Fine raised for {overdue_days} overdue day(s)." if overdue_days > 0 else "No fine."),
            alert=True
        )

    def _create_fine(self, overdue_days):
        if self.fine_created:
            return

        settings = frappe.get_single("Library Settings")
        fine_per_day = settings.fine_per_day or 5
        total_fine = fine_per_day * overdue_days

        fine = frappe.get_doc({
            "doctype": "Library Fine",
            "member": self.member,
            "book_issue": self.name,
            "overdue_days": overdue_days,
            "fine_per_day": fine_per_day,
            "total_fine": total_fine,
            "paid_amount": 0,
            "status": "Unpaid"
        })
        fine.insert(ignore_permissions=True)
        self.db_set("fine_created", 1)

        frappe.msgprint(
            f"Fine of ₹{total_fine} created for {overdue_days} overdue day(s).",
            alert=True
        )