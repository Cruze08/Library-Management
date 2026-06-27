frappe.query_reports["Book Utilization Report"] = {
    filters: [
        {
            fieldname: "category",
            label: "Category",
            fieldtype: "Link",
            options: "Book Category"
        }
    ]
};