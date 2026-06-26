# library_management/library_management/tasks.py
import frappe
from frappe.utils import today, getdate


def mark_overdue_issues():
    """
    Runs daily at midnight via scheduler_events in hooks.py.
    Marks all submitted Book Issues as Overdue if due_date has passed
    and the book hasn't been returned yet.
    """
    overdue_issues = frappe.get_all(
        "Book Issue",
        filters={
            "status": "Issued",
            "due_date": ["<", today()],
            "docstatus": 1
        },
        fields=["name", "member", "book", "due_date"]
    )

    if not overdue_issues:
        return

    for issue in overdue_issues:
        frappe.db.set_value("Book Issue", issue["name"], "status", "Overdue")
        _send_overdue_email(issue)

    frappe.db.commit()
    frappe.logger().info(
        f"[Library] Marked {len(overdue_issues)} issues as Overdue."
    )


def _send_overdue_email(issue):
    """Send an overdue reminder email to the member."""
    member = frappe.get_doc("Library Member", issue["member"])
    if not member.email:
        return

    book_title = frappe.db.get_value("Book", issue["book"], "title")
    settings = frappe.get_single("Library Settings")
    days_overdue = (getdate(today()) - getdate(issue["due_date"])).days
    fine_accrued = days_overdue * (settings.fine_per_day or 5)

    frappe.sendmail(
        recipients=[member.email],
        subject=f"Overdue Book Reminder — {book_title}",
        message=f"""
        <p>Dear {member.full_name},</p>
        <p>
            The book <strong>{book_title}</strong> was due on
            <strong>{issue['due_date']}</strong> and is now
            <strong>{days_overdue} day(s) overdue</strong>.
        </p>
        <p>
            Fine accrued so far: <strong>₹{fine_accrued}</strong>
            (₹{settings.fine_per_day or 5}/day).
        </p>
        <p>Please return the book at the earliest to avoid further charges.</p>
        <br>
        <p>Library Team</p>
        """,
        now=True
    )