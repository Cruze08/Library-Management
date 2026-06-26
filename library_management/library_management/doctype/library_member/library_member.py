# library_management/library_management/doctype/library_member/library_member.py
import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate


class LibraryMember(Document):

    def before_save(self):
        self._check_membership_expiry()

    def after_insert(self):
        self._create_customer()

    def _check_membership_expiry(self):
        if self.membership_end:
            self.is_expired = 1 if getdate(self.membership_end) < getdate(today()) else 0

    def _create_customer(self):
        """Auto-create an ERPNext Customer so GL entries work out of the box."""
        if self.customer:
            return

        if not frappe.db.exists("DocType", "Customer"):
            return  # ERPNext not installed — skip

        # Ensure Customer Group exists
        if not frappe.db.exists("Customer Group", "Library Members"):
            frappe.get_doc({
                "doctype": "Customer Group",
                "customer_group_name": "Library Members",
                "parent_customer_group": "All Customer Groups"
            }).insert(ignore_permissions=True)

        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": self.full_name,
            "customer_type": "Individual",
            "customer_group": "Library Members",
            "territory": "All Territories",
        })
        customer.insert(ignore_permissions=True)

        self.db_set("customer", customer.name)
        frappe.msgprint(
            f"ERPNext Customer <b>{customer.name}</b> created and linked.",
            alert=True
        )

    def update_outstanding_fine(self):
        """Recalculate and save outstanding fine balance."""
        total = frappe.db.sql("""
            SELECT COALESCE(SUM(total_fine - paid_amount), 0)
            FROM `tabLibrary Fine`
            WHERE member = %s
              AND status NOT IN ('Paid', 'Waived')
        """, self.name)[0][0]

        self.db_set("outstanding_fine", total)

    @staticmethod
    def validate_membership(member_name):
        """Raise if member's membership is expired."""
        member = frappe.get_doc("Library Member", member_name)
        if member.is_expired:
            frappe.throw(
                f"Membership of <b>{member.full_name}</b> has expired "
                f"(valid until {member.membership_end}). "
                "Please renew before issuing books."
            )