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
        {"label": "Member",          "fieldname": "member",        "fieldtype": "Link",     "options": "Library Member","width": 130},
        {"label": "Member Name",     "fieldname": "member_name",   "fieldtype": "Data",     "width": 160},
        {"label": "Member Type",     "fieldname": "member_type",   "fieldtype": "Data",     "width": 100},
        {"label": "Email",           "fieldname": "email",         "fieldtype": "Data",     "width": 160},
        {"label": "Total Fines",     "fieldname": "total_fines",   "fieldtype": "Currency", "width": 120},
        {"label": "Paid",            "fieldname": "paid",          "fieldtype": "Currency", "width": 110},
        {"label": "Waived",          "fieldname": "waived",        "fieldtype": "Currency", "width": 110},
        {"label": "Outstanding",     "fieldname": "outstanding",   "fieldtype": "Currency", "width": 120},
        {"label": "Unpaid Count",    "fieldname": "unpaid_count",  "fieldtype": "Int",      "width": 110},
    ]


def get_data(filters):
    conditions = "lf.docstatus = 1 AND lf.status != 'Paid'"
    if filters.get("member_type"):
        conditions += " AND lm.member_type = %(member_type)s"

    return frappe.db.sql(f"""
        SELECT
            lm.name                             AS member,
            lm.full_name                        AS member_name,
            lm.member_type,
            lm.email,
            SUM(lf.total_fine)                  AS total_fines,
            SUM(lf.paid_amount)                 AS paid,
            SUM(lf.waiver_amount)               AS waived,
            SUM(lf.outstanding_amount)          AS outstanding,
            COUNT(lf.name)                      AS unpaid_count
        FROM
            `tabLibrary Fine` lf
            JOIN `tabLibrary Member` lm ON lm.name = lf.member
        WHERE {conditions}
        GROUP BY lm.name
        HAVING outstanding > 0
        ORDER BY outstanding DESC
    """, filters, as_dict=True)


def get_chart(data):
    top = data[:8]
    return {
        "data": {
            "labels":   [d["member_name"] for d in top],
            "datasets": [{"name": "Outstanding", "values": [flt(d["outstanding"]) for d in top]}]
        },
        "type": "pie",
        "colors": ["#e74c3c","#e67e22","#f1c40f","#2ecc71","#3498db","#9b59b6","#1abc9c","#e91e63"],
    }


def get_summary(data):
    return [
        {"label": "Members with Outstanding Fines", "value": len(data),                               "datatype": "Int",      "indicator": "Red"},
        {"label": "Total Outstanding Amount",        "value": sum(flt(d["outstanding"]) for d in data),"datatype": "Currency", "indicator": "Red"},
        {"label": "Total Unpaid Fine Records",       "value": sum(d["unpaid_count"] for d in data),   "datatype": "Int",      "indicator": "Orange"},
    ]