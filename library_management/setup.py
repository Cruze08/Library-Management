import frappe
from frappe.utils import today, add_days


def after_install():
    print("\n── Library Management: Running setup ──────────────────────")
    _create_roles()
    _create_library_settings()
    _create_book_categories()
    _create_books()
    _create_demo_members()
    _create_number_cards()
    _create_dashboard_charts()
    _create_dashboard()
    print("── Library Management: Setup complete! ────────────────────\n")


def _create_roles():
    roles = ["Library Administrator", "Library Staff", "Accounts Staff", "Management"]
    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    print("  ✓ Roles created")


def _create_library_settings():
    settings = frappe.get_single("Library Settings")
    if not settings.loan_period_days:
        settings.loan_period_days = 14
        settings.fine_per_day = 5
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        print("  ✓ Library Settings configured")
    else:
        print("  ↩ Library Settings already configured")


def _create_book_categories():
    categories = ["Science", "Fiction", "Technology", "History", "Self Help"]
    for cat in categories:
        if not frappe.db.exists("Book Category", cat):
            frappe.get_doc({
                "doctype": "Book Category",
                "category_name": cat
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    print("  ✓ Book Categories created")


def _create_books():
    books = [
        {"isbn": "9780553380163", "title": "A Brief History of Time", "author": "Stephen Hawking",  "category": "Science",    "rack_location": "A-01", "total_copies": 3},
        {"isbn": "9780062315007", "title": "The Alchemist",           "author": "Paulo Coelho",     "category": "Fiction",    "rack_location": "B-05", "total_copies": 2},
        {"isbn": "9780132350884", "title": "Clean Code",              "author": "Robert C. Martin", "category": "Technology", "rack_location": "C-12", "total_copies": 2},
        {"isbn": "9780062316097", "title": "Sapiens",                 "author": "Yuval Noah Harari","category": "Science",    "rack_location": "A-08", "total_copies": 1},
        {"isbn": "9780743273565", "title": "The Great Gatsby",        "author": "F. Scott Fitzgerald","category": "Fiction",  "rack_location": "B-10", "total_copies": 2},
    ]
    created = 0
    for data in books:
        if not frappe.db.exists("Book", data["isbn"]):
            frappe.get_doc({"doctype": "Book", **data}).insert(ignore_permissions=True)
            created += 1
    frappe.db.commit()
    print(f"  ✓ {created} Books created")


def _create_demo_members():
    if frappe.db.count("Library Member") > 0:
        print("  ↩ Members already exist — skipping")
        return

    if frappe.db.exists("DocType", "Customer"):
        if not frappe.db.exists("Customer Group", "Library Members"):
            frappe.get_doc({
                "doctype": "Customer Group",
                "customer_group_name": "Library Members",
                "parent_customer_group": "All Customer Groups"
            }).insert(ignore_permissions=True)
            frappe.db.commit()

    members = [
        {"full_name": "Raj Patel",   "member_type": "Student", "email": "raj@demo.com",   "phone": "9876543210", "membership_start": "2026-01-01", "membership_end": "2026-12-31"},
        {"full_name": "Priya Shah",  "member_type": "Staff",   "email": "priya@demo.com", "phone": "9876543211", "membership_start": "2026-01-01", "membership_end": "2026-12-31"},
        {"full_name": "Amit Desai",  "member_type": "Public",  "email": "amit@demo.com",  "phone": "9876543212", "membership_start": "2026-01-01", "membership_end": "2026-12-31"},
    ]
    for data in members:
        frappe.get_doc({"doctype": "Library Member", **data}).insert(ignore_permissions=True)
        frappe.db.commit()
    print("  ✓ 3 Demo Members created")


def _create_number_cards():
    cards = [
        {
            "name": "Total Books",
            "label": "Total Books",
            "document_type": "Book",
            "type": "Document Type",
            "function": "Count",
            "is_standard": 1,
            "module": "Library Management",
            "color": "#5e64ff",
            "filters_json": "[]",
        },
        {
            "name": "Overdue Books",
            "label": "Overdue Books",
            "document_type": "Book Issue",
            "type": "Document Type",
            "function": "Count",
            "is_standard": 1,
            "module": "Library Management",
            "color": "#e74c3c",
            "filters_json": '[["Book Issue","status","=","Overdue"],["Book Issue","docstatus","=","1"]]',
        },
        {
            "name": "Active Members",
            "label": "Active Members",
            "document_type": "Library Member",
            "type": "Document Type",
            "function": "Count",
            "is_standard": 1,
            "module": "Library Management",
            "color": "#00b894",
            "filters_json": '[["Library Member","is_expired","=","0"]]',
        },
        {
            "name": "Outstanding Fines",
            "label": "Outstanding Fines",
            "document_type": "Library Fine",
            "type": "Document Type",
            "function": "Sum",
            "aggregate_function_based_on": "outstanding_amount",
            "is_standard": 1,
            "module": "Library Management",
            "color": "#f39c12",
            "filters_json": '[["Library Fine","docstatus","=","1"],["Library Fine","status","not in","Paid,Waived"]]',
        },
    ]

    for card in cards:
        if not frappe.db.exists("Number Card", card["name"]):
            frappe.get_doc({"doctype": "Number Card", **card}).insert(ignore_permissions=True)
            print(f"  ✓ Number Card: {card['name']}")
        else:
            print(f"  ↩ Number Card exists: {card['name']}")

    frappe.db.commit()


def _create_dashboard_charts():
    charts = [
        {
            "name": "Book Issue Trend",
            "chart_name": "Book Issue Trend",
            "chart_type": "Count",
            "document_type": "Book Issue",
            "based_on": "issue_date",
            "timespan": "Last 3 Months",
            "time_interval": "Weekly",
            "type": "Line",
            "color": "#5e64ff",
            "is_standard": 1,
            "module": "Library Management",
            "filters_json": '[["Book Issue","docstatus","=","1"]]',
        },
        {
            "name": "Fine Collection Trend",
            "chart_name": "Fine Collection Trend",
            "chart_type": "Sum",
            "document_type": "Library Fine",
            "based_on": "creation",
            "value_based_on": "paid_amount",
            "timespan": "Last 3 Months",
            "time_interval": "Weekly",
            "type": "Bar",
            "color": "#00b894",
            "is_standard": 1,
            "module": "Library Management",
            "filters_json": '[["Library Fine","docstatus","=","1"]]',
        },
    ]

    for chart in charts:
        if not frappe.db.exists("Dashboard Chart", chart["name"]):
            frappe.get_doc({"doctype": "Dashboard Chart", **chart}).insert(ignore_permissions=True)
            print(f"  ✓ Chart: {chart['name']}")
        else:
            print(f"  ↩ Chart exists: {chart['name']}")

    frappe.db.commit()


def _create_dashboard():
    if frappe.db.exists("Dashboard", "Library Dashboard"):
        print("  ↩ Dashboard already exists")
        return

    frappe.get_doc({
        "doctype": "Dashboard",
        "dashboard_name": "Library Dashboard",
        "module": "Library Management",
        "is_standard": 1,
        "cards": [
            {"card": "Total Books"},
            {"card": "Overdue Books"},
            {"card": "Active Members"},
            {"card": "Outstanding Fines"},
        ],
        "charts": [
            {"chart": "Book Issue Trend",      "width": "Full"},
            {"chart": "Fine Collection Trend", "width": "Full"},
        ],
    }).insert(ignore_permissions=True)

    frappe.db.commit()
    print("  ✓ Library Dashboard created")