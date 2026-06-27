frappe.query_reports["Fine Collection Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today()
        },
        {
            fieldname: "status",
            label: "Status",
            fieldtype: "Select",
            options: "\nUnpaid\nPartially Paid\nPaid\nWaived"
        },
        {
            fieldname: "member_type",
            label: "Member Type",
            fieldtype: "Select",
            options: "\nStudent\nStaff\nPublic"
        }
    ]
};