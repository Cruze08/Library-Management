import frappe
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data    = get_data(filters)
    chart   = get_chart(data)
    summary = get_summary(data)
    return columns, data, None, chart, summary


def get_columns():
    return [
        {"label": "Fine ID",       "fieldname": "name",          "fieldtype": "Link",     "options": "Library Fine", "width": 140},
        {"label": "Member",        "fieldname": "member",        "fieldtype": "Link",     "options": "Library Member","width": 140},
        {"label": "Member Name",   "fieldname": "member_name",   "fieldtype": "Data",     "width": 150},
        {"label": "Member Type",   "fieldname": "member_type",   "fieldtype": "Data",     "width": 100},
        {"label": "Book Issue",    "fieldname": "book_issue",    "fieldtype": "Link",     "options": "Book Issue",   "width": 140},
        {"label": "Overdue Days",  "fieldname": "overdue_days",  "fieldtype": "Int",      "width": 100},
        {"label": "Total Fine",    "fieldname": "total_fine",    "fieldtype": "Currency", "width": 110},
        {"label": "Paid Amount",   "fieldname": "paid_amount",   "fieldtype": "Currency", "width": 110},
        {"label": "Outstanding",   "fieldname": "outstanding_amount","fieldtype": "Currency","width": 110},
        {"label": "Status",        "fieldname": "status",        "fieldtype": "Data",     "width": 110},
        {"label": "Waiver Amount", "fieldname": "waiver_amount", "fieldtype": "Currency", "width": 110},
        {"label": "Waiver Reason", "fieldname": "waiver_reason", "fieldtype": "Data",     "width": 160},
    ]


def get_data(filters):
    conditions = "lf.docstatus = 1"

    if filters.get("from_date"):
        conditions += " AND lf.creation >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND lf.creation <= %(to_date)s"
    if filters.get("status"):
        conditions += " AND lf.status = %(status)s"
    if filters.get("member_type"):
        conditions += " AND lm.member_type = %(member_type)s"

    return frappe.db.sql(f"""
        SELECT
            lf.name,
            lf.member,
            lm.full_name AS member_name,
            lm.member_type,
            lf.book_issue,
            lf.overdue_days,
            lf.total_fine,
            lf.paid_amount,
            lf.outstanding_amount,
            lf.status,
            lf.waiver_amount,
            lf.waiver_reason
        FROM
            `tabLibrary Fine` lf
            LEFT JOIN `tabLibrary Member` lm ON lm.name = lf.member
        WHERE {conditions}
        ORDER BY lf.creation DESC
    """, filters, as_dict=True)


def get_chart(data):
    # Bar chart — total fine vs paid per fine record (top 10)
    top = data[:10]
    return {
        "data": {
            "labels":   [d["name"] for d in top],
            "datasets": [
                {"name": "Total Fine",  "values": [flt(d["total_fine"])  for d in top]},
                {"name": "Paid Amount", "values": [flt(d["paid_amount"]) for d in top]},
            ]
        },
        "type": "bar",
        "colors": ["#5e64ff", "#28a745"],
        "barOptions": {"stacked": False},
    }


def get_summary(data):
    total_fines     = sum(flt(d["total_fine"])         for d in data)
    total_collected = sum(flt(d["paid_amount"])         for d in data)
    total_waived    = sum(flt(d["waiver_amount"])       for d in data)
    total_outstanding = sum(flt(d["outstanding_amount"]) for d in data)

    return [
        {"label": "Total Fines Raised",    "value": total_fines,       "datatype": "Currency", "indicator": "Blue"},
        {"label": "Total Collected",        "value": total_collected,   "datatype": "Currency", "indicator": "Green"},
        {"label": "Total Waived",           "value": total_waived,      "datatype": "Currency", "indicator": "Orange"},
        {"label": "Total Outstanding",      "value": total_outstanding, "datatype": "Currency", "indicator": "Red"},
    ]