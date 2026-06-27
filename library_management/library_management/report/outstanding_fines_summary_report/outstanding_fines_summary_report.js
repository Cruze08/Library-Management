frappe.query_reports["Outstanding Fines Summary"] = {
    filters: [
        {
            fieldname: "member_type",
            label: "Member Type",
            fieldtype: "Select",
            options: "\nStudent\nStaff\nPublic"
        }
    ]
};