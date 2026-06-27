import frappe
from frappe.utils import date_diff, today, flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data    = get_data(filters)
    chart   = get_chart(data)
    summary = get_summary(data)
    return columns, data, None, chart, summary


def get_columns():
    return [
        {"label": "Issue ID",      "fieldname": "name",         "fieldtype": "Link",  "options": "Book Issue",    "width": 140},
        {"label": "Member",        "fieldname": "member",       "fieldtype": "Link",  "options": "Library Member","width": 130},
        {"label": "Member Name",   "fieldname": "member_name",  "fieldtype": "Data",  "width": 150},
        {"label": "Member Type",   "fieldname": "member_type",  "fieldtype": "Data",  "width": 100},
        {"label": "Book",          "fieldname": "book",         "fieldtype": "Link",  "options": "Book",          "width": 130},
        {"label": "Book Title",    "fieldname": "book_title",   "fieldtype": "Data",  "width": 180},
        {"label": "Issue Date",    "fieldname": "issue_date",   "fieldtype": "Date",  "width": 100},
        {"label": "Due Date",      "fieldname": "due_date",     "fieldtype": "Date",  "width": 100},
        {"label": "Days Overdue",  "fieldname": "days_overdue", "fieldtype": "Int",   "width": 110},
        {"label": "Fine Accrued",  "fieldname": "fine_accrued", "fieldtype": "Currency","width": 120},
        {"label": "Fine Created",  "fieldname": "fine_created", "fieldtype": "Check", "width": 100},
    ]


def get_data(filters):
    conditions = "bi.docstatus = 1 AND bi.status IN ('Issued', 'Overdue') AND bi.due_date < %(today)s"
    filters["today"] = today()

    if filters.get("member_type"):
        conditions += " AND lm.member_type = %(member_type)s"
    if filters.get("member"):
        conditions += " AND bi.member = %(member)s"

    rows = frappe.db.sql(f"""
        SELECT
            bi.name,
            bi.member,
            lm.full_name     AS member_name,
            lm.member_type,
            bi.book,
            b.title          AS book_title,
            bi.issue_date,
            bi.due_date,
            bi.fine_created
        FROM
            `tabBook Issue` bi
            LEFT JOIN `tabLibrary Member` lm ON lm.name  = bi.member
            LEFT JOIN `tabBook`           b  ON b.name   = bi.book
        WHERE {conditions}
        ORDER BY bi.due_date ASC
    """, filters, as_dict=True)

    settings      = frappe.get_single("Library Settings")
    fine_per_day  = flt(settings.fine_per_day or 5)

    for row in rows:
        row["days_overdue"] = date_diff(today(), row["due_date"])
        row["fine_accrued"] = row["days_overdue"] * fine_per_day

    return rows


def get_chart(data):
    # Show top 10 most overdue members
    top = sorted(data, key=lambda x: x["days_overdue"], reverse=True)[:10]
    return {
        "data": {
            "labels":   [d["member_name"] for d in top],
            "datasets": [{"name": "Days Overdue", "values": [d["days_overdue"] for d in top]}]
        },
        "type": "bar",
        "colors": ["#e74c3c"],
    }


def get_summary(data):
    return [
        {"label": "Total Overdue Books",     "value": len(data),                                          "datatype": "Int",      "indicator": "Red"},
        {"label": "Avg Days Overdue",        "value": round(sum(d["days_overdue"] for d in data) / len(data), 1) if data else 0, "datatype": "Float","indicator": "Orange"},
        {"label": "Total Fine Accrued",      "value": sum(flt(d["fine_accrued"]) for d in data),          "datatype": "Currency", "indicator": "Red"},
        {"label": "Fines Already Created",   "value": sum(1 for d in data if d["fine_created"]),          "datatype": "Int",      "indicator": "Blue"},
    ]