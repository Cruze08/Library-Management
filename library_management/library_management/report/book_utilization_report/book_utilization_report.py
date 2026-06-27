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
        {"label": "Book",             "fieldname": "book",             "fieldtype": "Link", "options": "Book","width": 130},
        {"label": "Title",            "fieldname": "title",            "fieldtype": "Data", "width": 200},
        {"label": "Author",           "fieldname": "author",           "fieldtype": "Data", "width": 150},
        {"label": "Category",         "fieldname": "category",         "fieldtype": "Link", "options": "Book Category","width": 120},
        {"label": "Total Copies",     "fieldname": "total_copies",     "fieldtype": "Int",  "width": 100},
        {"label": "Available Copies", "fieldname": "available_copies", "fieldtype": "Int",  "width": 130},
        {"label": "Times Issued",     "fieldname": "times_issued",     "fieldtype": "Int",  "width": 110},
        {"label": "Currently Issued", "fieldname": "currently_issued", "fieldtype": "Int",  "width": 130},
        {"label": "Times Overdue",    "fieldname": "times_overdue",    "fieldtype": "Int",  "width": 120},
        {"label": "Utilization %",    "fieldname": "utilization_pct",  "fieldtype": "Percent","width": 120},
    ]


def get_data(filters):
    conditions = "1=1"
    if filters.get("category"):
        conditions += " AND b.category = %(category)s"

    rows = frappe.db.sql(f"""
        SELECT
            b.name                              AS book,
            b.title,
            b.author,
            b.category,
            b.total_copies,
            b.available_copies,
            COUNT(bi.name)                      AS times_issued,
            SUM(bi.status = 'Issued')           AS currently_issued,
            SUM(bi.status = 'Overdue')          AS times_overdue
        FROM
            `tabBook` b
            LEFT JOIN `tabBook Issue` bi ON bi.book = b.name AND bi.docstatus = 1
        WHERE {conditions}
        GROUP BY b.name
        ORDER BY times_issued DESC
    """, filters, as_dict=True)

    for row in rows:
        total = row["total_copies"] or 1
        row["utilization_pct"] = round(
            (flt(row["times_issued"]) / total) * 100, 2
        )

    return rows


def get_chart(data):
    top = data[:10]
    return {
        "data": {
            "labels":   [d["title"][:25] for d in top],
            "datasets": [{"name": "Times Issued", "values": [d["times_issued"] for d in top]}]
        },
        "type": "bar",
        "colors": ["#00b894"],
    }


def get_summary(data):
    return [
        {"label": "Total Books",        "value": len(data),                                       "datatype": "Int",     "indicator": "Blue"},
        {"label": "Total Issues",       "value": sum(d["times_issued"] for d in data),            "datatype": "Int",     "indicator": "Green"},
        {"label": "Currently Issued",   "value": sum(d["currently_issued"] or 0 for d in data),  "datatype": "Int",     "indicator": "Orange"},
        {"label": "Never Issued Books", "value": sum(1 for d in data if d["times_issued"] == 0), "datatype": "Int",     "indicator": "Red"},
    ]