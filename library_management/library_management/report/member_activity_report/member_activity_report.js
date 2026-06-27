frappe.query_reports["Member Activity Report"] = {
    filters: [
        {
            fieldname: "member_type",
            label: "Member Type",
            fieldtype: "Select",
            options: "\nStudent\nStaff\nPublic"
        },
        {
            fieldname: "is_expired",
            label: "Expired Only",
            fieldtype: "Check",
            default: 0
        }
    ]
};