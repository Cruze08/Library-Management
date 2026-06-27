frappe.query_reports["Overdue Books Report"] = {
    filters: [
        {
            fieldname: "member_type",
            label: "Member Type",
            fieldtype: "Select",
            options: "\nStudent\nStaff\nPublic"
        },
        {
            fieldname: "member",
            label: "Member",
            fieldtype: "Link",
            options: "Library Member"
        }
    ]
};