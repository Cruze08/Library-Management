# library_management/library_management/doctype/book/book.py
import frappe
from frappe.model.document import Document

class Book(Document):

    def before_save(self):
        # On first save, set available_copies = total_copies
        if self.is_new():
            self.available_copies = self.total_copies
        self._update_status()

    def _update_status(self):
        self.status = "Available" if self.available_copies > 0 else "Unavailable"

    def increment_available(self):
        """Call this when a book is returned."""
        self.available_copies = min(
            (self.available_copies or 0) + 1,
            self.total_copies
        )
        self._update_status()
        self.save(ignore_permissions=True)

    def decrement_available(self):
        """Call this when a book is issued."""
        if (self.available_copies or 0) < 1:
            frappe.throw(
                f"No copies of <b>{self.title}</b> are currently available."
            )
        self.available_copies -= 1
        self._update_status()
        self.save(ignore_permissions=True)