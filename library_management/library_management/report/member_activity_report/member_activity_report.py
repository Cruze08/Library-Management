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
        {"label": "Member",           "fieldname": "member",       "fieldtype": "Link",     "options": "Library Member","width": 130},
        {"label": "Member Name",      "fieldname": "member_name",  "fieldtype": "Data",     "width": 160},
        {"label": "Member Type",      "fieldname": "member_type",  "fieldtype": "Data",     "width": 100},
        {"label": "Total Issues",     "fieldname": "total_issues", "fieldtype": "Int",      "width": 110},
        {"label": "Returned",         "fieldname": "returned",     "fieldtype": "Int",      "width": 100},
        {"label": "Overdue",          "fieldname": "overdue",      "fieldtype": "Int",      "width": 100},
        {"label": "Currently Issued", "fieldname": "active",       "fieldtype": "Int",      "width": 130},
        {"label": "Total Fines",      "fieldname": "total_fines",  "fieldtype": "Currency", "width": 120},
        {"label": "Fines Paid",       "fieldname": "fines_paid",   "fieldtype": "Currency", "width": 120},
        {"label": "Outstanding Fine", "fieldname": "outstanding",  "fieldtype": "Currency", "width": 130},
        {"label": "Membership End",   "fieldname": "membership_end","fieldtype": "Date",    "width": 120},
        {"label": "Expired",          "fieldname": "is_expired",   "fieldtype": "Check",    "width": 80},
    ]


def get_data(filters):
    conditions = "1=1"
    if filters.get("member_type"):
        conditions += " AND lm.member_type = %(member_type)s"
    if filters.get("is_expired"):
        conditions += " AND lm.is_expired = 1"

    return frappe.db.sql(f"""
        SELECT
            lm.name                                         AS member,
            lm.full_name                                    AS member_name,
            lm.member_type,
            COUNT(bi.name)                                  AS total_issues,
            SUM(bi.status = 'Returned')                     AS returned,
            SUM(bi.status = 'Overdue')                      AS overdue,
            SUM(bi.status = 'Issued')                       AS active,
            COALESCE(SUM(lf.total_fine), 0)                 AS total_fines,
            COALESCE(SUM(lf.paid_amount), 0)                AS fines_paid,
            lm.outstanding_fine                             AS outstanding,
            lm.membership_end,
            lm.is_expired
        FROM
            `tabLibrary Member` lm
            LEFT JOIN `tabBook Issue`  bi ON bi.member = lm.name AND bi.docstatus = 1
            LEFT JOIN `tabLibrary Fine` lf ON lf.member = lm.name AND lf.docstatus = 1
        WHERE {conditions}
        GROUP BY lm.name
        ORDER BY total_issues DESC
    """, filters, as_dict=True)


def get_chart(data):
    top = data[:10]
    return {
        "data": {
            "labels":   [d["member_name"] for d in top],
            "datasets": [{"name": "Total Issues", "values": [d["total_issues"] for d in top]}]
        },
        "type": "bar",
        "colors": ["#5e64ff"],
    }


def get_summary(data):
    return [
        {"label": "Total Members",    "value": len(data),                                     "datatype": "Int",      "indicator": "Blue"},
        {"label": "Active Members",   "value": sum(1 for d in data if d["total_issues"] > 0), "datatype": "Int",      "indicator": "Green"},
        {"label": "Expired Members",  "value": sum(1 for d in data if d["is_expired"]),        "datatype": "Int",      "indicator": "Red"},
        {"label": "Total Outstanding","value": sum(flt(d["outstanding"]) for d in data),       "datatype": "Currency", "indicator": "Orange"},
    ]