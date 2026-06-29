# 📚 Library Management System
### Built on Frappe Framework | Developed by Ankit.

A complete Library Management System with book catalog, member management, issue & return tracking, fine collection, automated GL accounting entries, reports, and a live dashboard — all built as a custom Frappe app.

---

## 🚀 Features

| Module | What it does |
|---|---|
| **Book Catalog** | Manage books, categories, rack locations, copy tracking |
| **Member Management** | Register Student / Staff / Public members with validity tracking |
| **Book Issue & Return** | Issue books, auto due-date, one-click return, overdue detection |
| **Fine Management** | Auto-calculate fines on return, partial payments, waivers |
| **Accounting Integration** | Auto GL Journal Entries on fine raise and payment |
| **Reports** | 5 script reports with filters, charts, and summary KPIs |
| **Dashboard** | Live number cards + trend charts |

---

## ⚙️ Requirements

| Requirement | Version |
|---|---|
| Frappe Framework | v15+ |
| ERPNext (optional) | v15+ (needed for GL entries) |
| Python | 3.10+ |
| MariaDB | 10.6+ |

> **Note:** The app works without ERPNext. GL Journal Entry posting is skipped if ERPNext is not installed, but all library operations (issue, return, fine, payment) work fully.

---

## 📦 Installation

### 1. Get the app

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
```

### 2. Install on your site

```bash
bench install-app library_management
```

This automatically:
- Creates all doctypes and database tables
- Sets up 4 roles (Library Administrator, Library Staff, Accounts Staff, Management)
- Loads fixture data (Book Categories, Dashboard, Reports, Number Cards)
- Creates demo books and members for testing
- Configures default Library Settings (14-day loan, ₹5/day fine)

### 3. Migrate and restart

```bash
bench --site yoursite.local migrate
bench restart
```

### 4. Open the app

Go to your site → Desk → search **Library Management** in the module list.

---

## 🔧 Initial Configuration

### Set up Library Settings

> Desk → Awesome Bar → **Library Settings**

| Field | Recommended Value | Description |
|---|---|---|
| Loan Period Days | `14` | Days before a book becomes overdue |
| Fine Per Day | `5` | Fine amount (₹) charged per overdue day |
| Fine Income Account | `Library Fine Income - XX` | GL account for fine income (ERPNext only) |
| Fine Receivable Account | `Debtors - XX` | GL account for fine receivables (ERPNext only) |

> If you are not using ERPNext accounting, leave the GL account fields blank.

### Create GL Accounts (ERPNext only)

Go to **Chart of Accounts** and create:

```
Income
└── Library Fine Income          (Account Type: Income)

Current Assets
└── Library Fine Receivable      (Account Type: Receivable)
```

Then link them in Library Settings.

---

## 📋 How to Use

### Step 1 — Add Book Categories

> Desk → **Book Category** → New

Add your library's categories. Default categories installed:
`Science`, `Fiction`, `Technology`, `History`, `Self Help`

---

### Step 2 — Add Books

> Desk → **Book** → New

| Field | Description |
|---|---|
| Title | Book name |
| ISBN | Unique identifier (used as document name) |
| Author | Author name |
| Category | Link to Book Category |
| Rack Location | Physical shelf (e.g. A-01, B-05) |
| Total Copies | How many copies the library owns |
| Available Copies | Auto-managed — do not edit manually |
| Status | Auto-set: Available / Unavailable |

> ✅ Available Copies auto-fills = Total Copies on first save.
> ✅ Available Copies auto-updates every time a book is issued or returned.

---

### Step 3 — Register Members

> Desk → **Library Member** → New

| Field | Description |
|---|---|
| Full Name | Member's full name |
| Member Type | Student / Staff / Public |
| Email | Used for overdue reminder emails |
| Phone | Contact number |
| Membership Start | Membership validity start date |
| Membership End | Membership validity end date |
| Outstanding Fine | Auto-calculated — read only |
| ERPNext Customer | Auto-created on save (for GL entries) |

> ✅ Each member automatically creates an ERPNext Customer on save.
> ✅ Expired members are blocked from borrowing books.

**Member naming:** Members are auto-named as `LM-0001`, `LM-0002`, etc.

---

### Step 4 — Issue a Book

> Desk → **Book Issue** → New

| Field | Description |
|---|---|
| Member | Link to Library Member |
| Book | Link to Book (only available books shown) |
| Issue Date | Auto-set to today |
| Due Date | Auto-set = Issue Date + Loan Period Days |

**To issue:**
1. Select Member and Book
2. Save → Due Date auto-populates
3. Click **Submit**
4. Book's Available Copies decrements automatically

**Validations on issue:**
- Blocks if member's membership is expired
- Blocks if no copies are available
- Blocks if return date is before issue date

---

### Step 5 — Return a Book

To return a book, run this from **Bench Console** or a custom button:

```python
import frappe
issue = frappe.get_doc("Book Issue", "BI-2026-XXXX")
issue.process_return()
frappe.db.commit()
```

**What happens on return:**
- Return Date is set to today
- If returned before due date → Status = `Returned`, no fine
- If returned after due date → Status = `Overdue`, fine auto-created
- Book's Available Copies increments back

---

### Step 6 — Fine Management

Fines are created automatically on overdue return.

> Desk → **Library Fine** → open the fine record

**Fine lifecycle:**

```
Auto-created → Unpaid → Submit → Partially Paid → Paid
                                              └──→ Waived
```

**Submit the fine:**
- Click Submit on the Library Fine record
- GL Entry auto-posts: `Dr. Fine Receivable / Cr. Fine Income`

**Record a payment:**

```python
import frappe
fine = frappe.get_doc("Library Fine", "LF-2026-XXXX")
fine.record_payment(amount=50)  # partial or full
frappe.db.commit()
```

Payment GL Entry auto-posts: `Dr. Cash / Cr. Fine Receivable`

**Apply a waiver:**

```python
import frappe
fine = frappe.get_doc("Library Fine", "LF-2026-XXXX")
fine.apply_waiver(waiver_amount=50, reason="First time offence")
frappe.db.commit()
```

**Fine status logic:**

| Condition | Status |
|---|---|
| Nothing paid | Unpaid |
| Partially paid | Partially Paid |
| Fully paid | Paid |
| Waiver = Total Fine | Waived |

---

### Step 7 — Overdue Detection (Automatic)

A scheduled job runs **every day at midnight** and:
1. Marks all submitted Book Issues as `Overdue` if due_date has passed
2. Sends overdue reminder emails to members with email addresses

The member's email shows: book title, days overdue, fine accrued so far.

To trigger manually:

```bash
bench --site yoursite.local execute library_management.tasks.mark_overdue_issues
```

---

## 📊 Reports

Access all reports from: **Desk → Awesome Bar → [Report Name]**

### 1. Fine Collection Report
Shows all fines with member details, overdue days, total fine, paid amount, outstanding, and status.

**Filters:** From Date, To Date, Status, Member Type

### 2. Overdue Books Report
All currently overdue book issues with days overdue and fine accruing per day.

**Filters:** Member Type, Member

### 3. Member Activity Report
Per-member summary of total issues, returns, overdue count, fines raised, and outstanding balance.

**Filters:** Member Type, Expired Only

### 4. Book Utilization Report
Per-book summary of how many times issued, currently issued, times overdue, and utilization %.

**Filters:** Category

### 5. Outstanding Fines Summary
Members with unpaid/partially paid fines — sorted by outstanding amount.

**Filters:** Member Type

---

## 📈 Dashboard

> Desk → **Dashboard** → **Library Dashboard**

### Number Cards
| Card | What it shows |
|---|---|
| Total Books | Count of all books in catalog |
| Overdue Books | Book issues currently overdue |
| Active Members | Members with valid membership |
| Outstanding Fines | Sum of all unpaid fine amounts |

### Charts
| Chart | Type | Shows |
|---|---|---|
| Book Issue Trend | Line | Weekly issue count over last 3 months |
| Fine Collection Trend | Bar | Weekly fines raised vs collected |

---

## 👥 Roles & Permissions

| Role | Access |
|---|---|
| **Library Administrator** | Full access to all doctypes, settings, reports, waivers |
| **Library Staff** | Create/edit Book Issues, record fine payments, view members |
| **Accounts Staff** | Read-only on Library Fine and Journal Entries |
| **Management** | Reports and Dashboard only — no data entry |

**Assign roles:**
> Desk → User → [username] → Roles tab → add the relevant Library role

---

## 🗂️ Doctype Reference

| Doctype | Type | Description |
|---|---|---|
| Book Category | Master | Book classification |
| Book | Master | Book catalog with copy tracking |
| Library Member | Master | Member registration and profile |
| Library Settings | Single | Global configuration |
| Book Issue | Submittable | Book issue and return lifecycle |
| Library Fine | Submittable | Fine tracking with GL integration |

---

## 🐛 Troubleshooting

### Book copies not updating
```bash
bench --site yoursite.local migrate
bench restart
```

### Fine not created on return
- Check that `fine_per_day` is set in Library Settings
- Check that the book's `due_date` is in the past
- Verify `fine_created` field on Book Issue is `0`

### GL Entry not posting
- Check that `fine_income_account` and `receivable_account` are set in Library Settings
- Verify the accounts exist in your Chart of Accounts
- Check that a default Company is set in Global Defaults

### Overdue emails not sending
- Check that the member has an email address
- Verify Frappe email settings: **Desk → Email Account**
- Run the job manually:
```bash
bench --site yoursite.local execute library_management.tasks.mark_overdue_issues
```

### Member creation fails
```python
# Ensure Customer Group exists
import frappe
if not frappe.db.exists("Customer Group", "Library Members"):
    frappe.get_doc({
        "doctype": "Customer Group",
        "customer_group_name": "Library Members",
        "parent_customer_group": "All Customer Groups"
    }).insert(ignore_permissions=True)
    frappe.db.commit()
```

---

## 📁 App Structure

```
library_management/
├── library_management/
│   ├── hooks.py                          # App config, scheduler, fixtures
│   ├── setup.py                          # After-install demo data
│   ├── tasks.py                          # Scheduled jobs
│   └── library_management/
│       ├── doctype/
│       │   ├── book_category/
│       │   ├── book/
│       │   ├── library_member/
│       │   ├── library_settings/
│       │   ├── book_issue/
│       │   └── library_fine/
│       ├── report/
│       │   ├── fine_collection_report/
│       │   ├── overdue_books_report/
│       │   ├── member_activity_report/
│       │   ├── book_utilization_report/
│       │   └── outstanding_fines_summary/
│       └── dashboard/
│           └── library_dashboard/
├── fixtures/
│   ├── book_category.json
│   ├── role.json
│   ├── number_card.json
│   ├── dashboard_chart.json
│   ├── dashboard.json
│   └── report.json
├── setup.py
└── README.md
```

---

## 🔄 Uninstall

```bash
bench --site yoursite.local uninstall-app library_management
bench --site yoursite.local migrate
```

---

## 🤝 Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/library_management
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

---

## 📄 License

MIT License — free to use, modify, and distribute.


Thanku