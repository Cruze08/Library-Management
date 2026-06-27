# library_management/setup.py
import frappe
from frappe.utils import today, add_days


def after_install():
    """
    Runs automatically after: bench install-app library_management
    Creates roles, demo books, members, settings.
    """
    print("\n── Library Management: Running setup ──────────────────────")
    _create_roles()
    _create_library_settings()
    _create_book_categories()
    _create_books()
    _create_demo_members()
    print("── Library Management: Setup complete! ────────────────────\n")


# ── Roles ─────────────────────────────────────────────────────────────

def _create_roles():
    roles = [
        "Library Administrator",
        "Library Staff",
        "Accounts Staff",
        "Management",
    ]
    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    print("  ✓ Roles created")


# ── Library Settings ──────────────────────────────────────────────────

def _create_library_settings():
    settings = frappe.get_single("Library Settings")
    if not settings.loan_period_days:
        settings.loan_period_days = 14
        settings.fine_per_day = 5
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        print("  ✓ Library Settings configured (14 day loan, ₹5/day fine)")
    else:
        print("  ↩ Library Settings already configured")


# ── Book Categories ───────────────────────────────────────────────────

def _create_book_categories():
    categories = ["Science", "Fiction", "Technology", "History", "Self Help"]
    for cat in categories:
        if not frappe.db.exists("Book Category", cat):
            frappe.get_doc({
                "doctype": "Book Category",
                "category_name": cat
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    print("  ✓ Book Categories created (Science, Fiction, Technology, History, Self Help)")


# ── Books ─────────────────────────────────────────────────────────────

def _create_books():
    books = [
        {
            "isbn": "9780553380163",
            "title": "A Brief History of Time",
            "author": "Stephen Hawking",
            "category": "Science",
            "rack_location": "A-01",
            "total_copies": 3,
        },
        {
            "isbn": "9780062315007",
            "title": "The Alchemist",
            "author": "Paulo Coelho",
            "category": "Fiction",
            "rack_location": "B-05",
            "total_copies": 2,
        },
        {
            "isbn": "9780132350884",
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "category": "Technology",
            "rack_location": "C-12",
            "total_copies": 2,
        },
        {
            "isbn": "9780062316097",
            "title": "Sapiens",
            "author": "Yuval Noah Harari",
            "category": "Science",
            "rack_location": "A-08",
            "total_copies": 1,
        },
        {
            "isbn": "9780743273565",
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "category": "Fiction",
            "rack_location": "B-10",
            "total_copies": 2,
        },
    ]

    created = 0
    for data in books:
        if not frappe.db.exists("Book", data["isbn"]):
            frappe.get_doc({"doctype": "Book", **data}).insert(ignore_permissions=True)
            created += 1
    frappe.db.commit()
    print(f"  ✓ {created} Books created")


# ── Demo Members ──────────────────────────────────────────────────────

def _create_demo_members():
    """
    Creates 3 demo members for testing.
    Only runs if no members exist yet.
    """
    if frappe.db.count("Library Member") > 0:
        print("  ↩ Members already exist — skipping demo member creation")
        return

    # Ensure Customer Group exists
    if frappe.db.exists("DocType", "Customer"):
        if not frappe.db.exists("Customer Group", "Library Members"):
            frappe.get_doc({
                "doctype": "Customer Group",
                "customer_group_name": "Library Members",
                "parent_customer_group": "All Customer Groups"
            }).insert(ignore_permissions=True)
            frappe.db.commit()

    members = [
        {
            "full_name": "Raj Patel",
            "member_type": "Student",
            "email": "raj@demo.com",
            "phone": "9876543210",
            "membership_start": "2026-01-01",
            "membership_end": "2026-12-31",
        },
        {
            "full_name": "Priya Shah",
            "member_type": "Staff",
            "email": "priya@demo.com",
            "phone": "9876543211",
            "membership_start": "2026-01-01",
            "membership_end": "2026-12-31",
        },
        {
            "full_name": "Amit Desai",
            "member_type": "Public",
            "email": "amit@demo.com",
            "phone": "9876543212",
            "membership_start": "2026-01-01",
            "membership_end": "2026-12-31",
        },
    ]

    for data in members:
        frappe.get_doc({"doctype": "Library Member", **data}).insert(ignore_permissions=True)
        frappe.db.commit()

    print("  ✓ 3 Demo Members created (Raj Patel, Priya Shah, Amit Desai)")