XYZ Fulfillment Hub

A practical warehouse and order-fulfillment visibility application built
as a take-home project.

XYZ Fulfillment Hub replaces spreadsheet-driven fulfillment tracking
with a single operational dashboard for orders, inventory, picking,
shipping, and issues.

The application is intentionally focused on visibility + action
rather than trying to become a complete enterprise warehouse-management
system.

1. Project Overview

The problem

The fulfillment process being modeled is:

Order Received
      ↓
Order Processed
      ↓
Picking
      ↓
Packing
      ↓
Staging
      ↓
Shipping

In the original scenario, fulfillment was managed using spreadsheets and
shared folders. This creates several operational problems:

It is difficult to see the current status of an order.

Delays can go unnoticed.

Priority orders can get mixed with regular orders.

Spreadsheet stock can become inaccurate or missing.

The wrong product or variant can sometimes be shipped.

Packed boxes can be misplaced.

Courier pickups can be missed.

Operational problems may be handled informally instead of being
tracked.

The solution

XYZ Fulfillment Hub provides one place to:

See the current fulfillment situation.

Identify orders requiring attention.

Track inventory availability.

Detect system-vs-physical stock mismatches.

Verify the correct product and variant during picking.

Track packages through staging and courier pickup.

Surface missed pickups.

Track operational issues and resolve them.

2. Main Features

Dashboard

The dashboard provides a high-level operational view.

It shows:

Total orders

Priority orders

Delayed orders

Open issues

Inventory mismatches

Product/picking mismatches

Fulfillment pipeline

Orders by channel

Operational issues

Priority orders requiring attention

The goal is to answer:

"What needs attention right now?"

Orders

The Orders page provides order-level visibility.

Features:

Search by order ID

Filter by status

Filter by priority

View delayed orders

View orders with product mismatches

View order details

View expected products

View picked products

Compare expected vs picked product/variant

View fulfillment progress

Example:

Expected Product
SKU-001
Blue

        vs

Picked Product
SKU-002
Red

        ↓

⚠️ Mismatch

Inventory

The Inventory page addresses inaccurate spreadsheet stock.

It shows:

System stock

Physical stock

Reserved stock

Available stock

Warehouse

Category

SKU

Product

Stock status

Stock states include:

OK
Low Stock
Out of Stock
Mismatch

Inventory mismatch

A mismatch is identified when:

System Stock != Physical Stock

For example:

System Stock:   25
Physical Stock: 18

Difference:     -7

⚠️ Inventory mismatch

This is deliberately kept as a simple operational safeguard instead of
creating a separate complex inventory reconciliation system.

Picking

The Picking page helps warehouse staff pick the correct item.

It shows:

Orders waiting for picking

Priority

Deadline

Timing

Expected product

Expected SKU

Expected variant

Quantity

The picker can select the product actually picked and enter the picked
variant.

The application compares:

Expected Product
        vs
Picked Product

Expected Variant
        vs
Picked Variant

If they differ:

⚠️ PICKING MISMATCH

If they match:

✅ Correct product and variant

Once all items are correct, the order can be moved to:

PICKING → PACKED

Shipping

The Shipping page provides visibility after picking.

Shipment stages supported by the application include:

READY
  ↓
STAGED
  ↓
PICKED_UP
  ↓
IN_TRANSIT
  ↓
DELIVERED

It also supports:

PICKUP_MISSED

The page shows:

Packed orders

Ready shipments

Staged shipments

Picked-up shipments

Missed pickups

Courier

Tracking number

Pickup time

Shipment status

Example operational alert:

🚨 Courier pickup was missed.
This shipment needs attention.

This directly addresses the problem of packed boxes being missed by the
courier.

Issues

The Issues page acts as a lightweight operational issue tracker.

Supported issue types:

INVENTORY_SHORTAGE

INVENTORY_MISMATCH

PICKING_MISMATCH

PICKING_DELAY

PACKING_DELAY

COURIER_DELAY

Supported severities:

CRITICAL

HIGH

MEDIUM

LOW

Supported statuses:

OPEN
  ↓
IN_PROGRESS
  ↓
RESOLVED

The page allows the team to see problems in one place rather than
handling them informally.

3. Technology Stack

Technology   Purpose

Python       Application language
Streamlit    Web application/UI
SQLite       Local relational database
SQLAlchemy   Database engine and SQL access
Pandas       Data retrieval and tabular processing
Plotly       Dashboard charts
Faker        Large dummy-data generation
Git/GitHub   Version control and submission

4. Architecture

The project follows a simple application structure:

Streamlit UI
     ↓
Page modules
     ↓
SQL queries / database operations
     ↓
SQLAlchemy
     ↓
SQLite database

There is no separate REST API because the assignment is primarily an
operational dashboard/prototype.

5. Project Structure

fulfillment-hub/
│
├── app.py
│
├── requirements.txt
├── README.md
├── .gitignore
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   ├── schema.py
│   └── fulfillment.db
│
├── data/
│   └── generate_data.py
│
├── pages/
│   ├── orders.py
│   ├── inventory.py
│   ├── picking.py
│   ├── shipping.py
│   └── issues.py
│
└── assets/

app.py

Main Streamlit entrypoint.

Responsibilities:

Configure Streamlit.

Configure global styling.

Display navigation.

Render the Dashboard.

Load individual operational pages.

Run the application from this file.

database/db.py

Creates the SQLAlchemy database engine.

The application currently uses:

SQLite

The database file is:

database/fulfillment.db

database/schema.py

Defines the database models/tables.

Main entities:

Product

Customer

Warehouse

Inventory

Order

OrderItem

Shipment

Issue

The schema is created using SQLAlchemy.

data/generate_data.py

Generates realistic dummy data for the prototype.

The current generator creates approximately:

2,000 products

10,000 customers

2 warehouses

4,000 inventory records

30,000 orders

60,000+ order items

30,000 shipments

2,000 issues

The generator also creates deliberate operational scenarios so the
application is easy to demonstrate.

6. Database Model

Product

Stores product information.

Important fields:

id
sku
name
category
brand
variant
price

Customer

Stores customer information.

Important fields:

id
name
email
phone
city
state

Warehouse

Stores warehouse information.

Important fields:

id
name
type
location

Inventory

Connects products to warehouses.

Important fields:

id
product_id
warehouse_id
system_stock
physical_stock
reserved_stock

Available stock is calculated as:

Available Stock =
System Stock - Reserved Stock

Order

Stores fulfillment orders.

Important fields:

id
customer_id
warehouse_id
channel
priority
status
created_at
deadline

Typical order priorities:

NORMAL
HIGH
URGENT

Typical order statuses include:

RECEIVED
PROCESSING
PICKING
PACKED
STAGED
SHIPPED
DELIVERED

OrderItem

Stores individual products inside an order.

Important fields:

id
order_id
product_id
quantity
picked_product_id
picked_variant

picked_product_id and picked_variant allow the picking page to
compare the expected item with what was actually picked.

Shipment

Stores shipping information.

Important fields:

id
order_id
courier
tracking_number
status
pickup_time

Shipment statuses include:

READY
STAGED
PICKED_UP
IN_TRANSIT
DELIVERED
PICKUP_MISSED

Issue

Stores operational problems.

Important fields:

id
order_id
type
severity
description
status
created_at

7. Dummy Data

The project uses generated data rather than requiring a real company
dataset.

The data generator uses:

Faker
random

A fixed seed is used so that the generated dataset is reproducible.

The generator also creates deliberate demonstration scenarios.

Demo Scenario 1 --- Urgent Order

An urgent order is created in the picking stage with a near deadline.

Purpose:

Demonstrate priority visibility.

Demo Scenario 2 --- Product Mismatch

An order contains an expected product but the picked product is
deliberately set to another product.

Purpose:

Demonstrate the picking safeguard.

Demo Scenario 3 --- Delayed Order

An order is created with a deadline already in the past.

Purpose:

Demonstrate delayed-order visibility.

Demo Scenario 4 --- Inventory Mismatch

One inventory record deliberately contains:

System Stock:   25
Physical Stock: 18
Reserved:        5

Purpose:

Demonstrate inaccurate spreadsheet stock.

8. Local Setup

Requirements

Recommended environment:

Python 3.12+
Git

The project should be run from the repository root.

Clone the repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd fulfillment-hub

Create virtual environment

macOS/Linux:

python3 -m venv venv

Activate:

source venv/bin/activate

Windows:

venv\Scripts\activate

Install dependencies

pip install -r requirements.txt

9. Generate the Database

If the database does not exist, generate the dummy dataset:

PYTHONPATH=. python3 data/generate_data.py

This creates:

database/fulfillment.db

Important:

Run this command from the project root.

10. Run the Application

From the project root:

PYTHONPATH=. python3 -m streamlit run app.py

Streamlit will display a local URL, normally similar to:

http://localhost:8501

Open that URL in a browser.

11. Why PYTHONPATH=. Is Used

The project uses imports such as:

from database.db import engine

Because database is a package inside the project root, Python needs
the repository root on its import path.

Running:

PYTHONPATH=. python3 -m streamlit run app.py

ensures the project root is available.

12. Development Workflow

Recommended workflow:

1. Activate virtual environment
2. Pull latest Git changes
3. Run the application
4. Make changes
5. Run syntax checks
6. Test the affected page
7. Test the full workflow
8. Commit
9. Push

Example:

source venv/bin/activate

PYTHONPATH=. python3 -m streamlit run app.py

13. Useful Validation Commands

Check a Python file:

python3 -m py_compile pages/orders.py

Check all application Python files:

python3 -m py_compile app.py database/db.py database/schema.py data/generate_data.py pages/orders.py pages/inventory.py pages/picking.py pages/shipping.py pages/issues.py

If there is no output, the syntax checks passed.

14. Reset the Demo Database

If the demo data gets changed during testing and you want to return to
the original generated dataset:

rm database/fulfillment.db

Then regenerate:

PYTHONPATH=. python3 data/generate_data.py

This gives you a fresh demo database.

15. Recommended Demo Flow

The strongest walkthrough is not to click every feature randomly.

Instead, tell one operational story.

Step 1 --- Dashboard

Start with:

"This is the operations view. Instead of checking multiple
spreadsheets, the team can immediately see priority orders, delays,
inventory mismatches and open issues."

Show:

Priority orders

Delayed orders

Inventory mismatch

Open issues

Step 2 --- Open an Urgent Order

Go to:

Orders

Show:

URGENT
PICKING
Near deadline

Explain:

"The team can identify this order before it becomes another unnoticed
delay."

Step 3 --- Check Inventory

Go to:

Inventory

Show the mismatch:

System:   25
Physical: 18

Explain:

"The system can expose situations where spreadsheet stock does not
match physical stock."

Step 4 --- Picking

Go to:

Picking

Show:

Expected Product
        vs
Picked Product

Intentionally demonstrate the mismatch.

Then correct it.

Explain:

"This is a lightweight safeguard before the wrong product reaches
packing."

Step 5 --- Shipping

Move the shipment through:

READY
 ↓
STAGED
 ↓
PICKED_UP
 ↓
IN_TRANSIT
 ↓
DELIVERED

Also demonstrate the missed-pickup state if useful.

Step 6 --- Issues

Finish by showing:

OPEN
 ↓
IN_PROGRESS
 ↓
RESOLVED

Explain:

"Operational problems now have a visible place to be tracked instead
of being handled informally."

16. Design Philosophy

The application intentionally does not attempt to solve every
warehouse-management problem.

The focus is:

Visibility

Know what is happening.

Prioritization

Know what needs attention first.

Verification

Catch simple mistakes before they become customer-facing problems.

Action

Give operators a clear next step.

The project therefore focuses on a small number of practical operational
problems instead of creating a large enterprise system.

17. Why These Features Were Selected

The original workflow has many possible areas for improvement.

This project prioritizes problems that can be demonstrated clearly in a
lightweight prototype:

Problem                                    Feature

Hard to see order status                   Orders + Dashboard
Delays go unnoticed                        Deadline/delay visibility
Priority orders mixed with normal orders   Priority sorting
Stock inaccurate                           Inventory comparison
Wrong product/variant shipped              Picking check
Packed boxes misplaced                     Staging visibility
Courier misses pickup                      Pickup status
Problems handled informally                Issues page

18. Project Scope

Included

Order visibility

Priority handling

Deadline visibility

Inventory visibility

Inventory mismatch detection

Picking verification

Shipment tracking

Staging visibility

Courier pickup visibility

Missed pickup visibility

Issue tracking

Large generated dataset

Interactive operational dashboard

Not included

Real courier API integration

Real payment processing

Real warehouse scanner integration

Production authentication

Real-time IoT tracking

ERP integration

Automated replenishment

Full warehouse-management-system functionality

These were intentionally kept outside the scope of the take-home
prototype.

19. Performance Notes

The prototype uses a large dummy dataset to demonstrate that the
interface can operate on more than a few sample rows.

For example:

30,000 orders
60,000+ order items
30,000 shipments

Individual UI tables intentionally limit displayed results to a
manageable number of rows while SQL filtering and ordering are performed
before the data reaches the UI.

20. Security Notes

This is a take-home prototype and does not contain sensitive production
credentials.

Do not commit:

.env
API keys
passwords
private credentials
cloud secrets

The SQLite database contains synthetic data only.

If the project is later converted into a production system,
authentication, authorization, database hosting, secrets management,
logging, backups, and audit controls should be added.

21. Deployment

Recommended deployment for this prototype: Streamlit Community Cloud

Streamlit Community Cloud can deploy directly from a GitHub repository
and supports requirements.txt. The deployment interface lets you
choose the repository, branch, and entrypoint file. Streamlit
deployment
documentation

The repository structure is already suitable because:

app.py
requirements.txt

are located at the project root.

Before deployment

Make sure:

python3 -m py_compile app.py

and:

python3 -m py_compile database/db.py database/schema.py data/generate_data.py

and:

python3 -m py_compile pages/orders.py pages/inventory.py pages/picking.py pages/shipping.py pages/issues.py

Then test locally:

PYTHONPATH=. python3 -m streamlit run app.py

Important SQLite deployment note

This prototype uses:

database/fulfillment.db

SQLite is appropriate for this take-home prototype.

However, SQLite is not the right database architecture for a multi-user
production fulfillment platform.

For a production version, migrate to a hosted relational database such
as PostgreSQL.

For the take-home demo, SQLite keeps the project simple and easy to run.

22. Deploy to Streamlit Community Cloud

1. Push the repository to GitHub

git add .
git commit -m "Initial XYZ Fulfillment Hub"
git push -u origin main

2. Open Streamlit Community Cloud

Go to:

https://share.streamlit.io/

Sign in with GitHub.

3. Create the application

Choose:

Create app

Then select:

Repository: YOUR_USERNAME/fulfillment-hub
Branch: main
Main file path: app.py

Streamlit's current deployment flow supports selecting the GitHub
repository, branch and entrypoint file. Official deployment
guide

4. Deploy

Click:

Deploy

Streamlit will install the dependencies from requirements.txt and
launch app.py.

5. Verify

Test:

Dashboard
Orders
Inventory
Picking
Shipping
Issues

The deployed application receives a streamlit.app URL. Streamlit
Community Cloud
documentation

23. GitHub Workflow After Deployment

Once the application is connected to Streamlit Community Cloud:

Local changes
     ↓
git add .
     ↓
git commit
     ↓
git push
     ↓
GitHub
     ↓
Streamlit Community Cloud
     ↓
Updated application

Community Cloud monitors the connected GitHub repository and updates the
deployed application after repository changes. Streamlit app management
documentation

24. Troubleshooting

ModuleNotFoundError: No module named 'database'

Run from the project root:

PYTHONPATH=. python3 -m streamlit run app.py

Do not run individual application modules from inside their
subdirectories.

ModuleNotFoundError for a Python package

Activate the virtual environment:

source venv/bin/activate

Then:

pip install -r requirements.txt

Database does not exist

Run:

PYTHONPATH=. python3 data/generate_data.py

Streamlit page does not appear

Check that app.py contains the corresponding page route.

Example:

elif page == "Inventory":
    exec(open("pages/inventory.py", encoding="utf-8").read())

Changes are not appearing

Stop Streamlit:

Ctrl + C

Then restart:

PYTHONPATH=. python3 -m streamlit run app.py

25. Git Commands

Initialize Git if necessary:

git init

Check status:

git status

Add files:

git add .

Commit:

git commit -m "Build XYZ Fulfillment Hub prototype"

Add GitHub remote:

git remote add origin https://github.com/YOUR_USERNAME/fulfillment-hub.git

Rename branch:

git branch -M main

Push:

git push -u origin main

For future changes:

git add .
git commit -m "Update fulfillment workflow"
git push

26. Suggested Commit History

If the repository is being submitted for evaluation, clean commits can
make the development process easier to understand.

Example:

Initial project setup
Add database schema
Add realistic fulfillment dataset
Build operations dashboard
Add order tracking
Add inventory visibility
Add picking verification
Add shipping workflow
Add issue tracking
Polish UI and documentation

A single final commit is also acceptable if the project was developed
locally first.

27. Future Improvements

If this prototype were developed further, possible improvements would
include:

PostgreSQL

Authentication and role-based access

Real warehouse barcode scanning

Real courier APIs

Automatic notifications

SLA monitoring

Audit logs

Inventory reconciliation workflow

Warehouse-level permissions

Automated replenishment suggestions

Real-time event processing

Background jobs

Production monitoring

Database backups

Automated tests

CI/CD

These are intentionally outside the current take-home scope.

28. Evaluation / Demo Focus

The project is designed to demonstrate four things:

1. Problem understanding

The application maps directly to operational problems in the provided
fulfillment scenario.

2. Practical judgment

The project does not attempt to build an entire enterprise WMS.

Instead, it focuses on high-value visibility and operational safeguards.

3. Clean usability

Operators can navigate from:

Problem
 ↓
Order
 ↓
Inventory
 ↓
Picking
 ↓
Shipping
 ↓
Issue resolution

4. Explainability

The system makes it easy to demonstrate why a particular feature exists
and what operational problem it addresses.

29. License

This project was created as a take-home assignment/prototype.

Unless otherwise specified, the project should be treated as
demonstration code rather than a production-ready commercial system.

30. Quick Start

For someone evaluating the project:

git clone <YOUR_GITHUB_REPOSITORY_URL>

cd fulfillment-hub

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

PYTHONPATH=. python3 data/generate_data.py

PYTHONPATH=. python3 -m streamlit run app.py

Then open:

http://localhost:8501

Start with:

Dashboard

and follow the operational flow:

Orders
→ Inventory
→ Picking
→ Shipping
→ Issues

31. Project Summary

XYZ Fulfillment Hub is a lightweight fulfillment operations
dashboard designed to replace fragmented spreadsheet-based visibility
with a single operational interface.

Its core principle is:

See the problem → understand the impact → take the next action.

The prototype focuses on order visibility, inventory accuracy, picking
verification, shipping visibility, and operational issue tracking while
remaining intentionally simple enough to demonstrate within a short
walkthrough.