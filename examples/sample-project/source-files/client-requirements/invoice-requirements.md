# Acme — AI Invoice Processing: Requirement Notes

## Background
Today our AP team receives supplier invoices by email (PDF attachments). A coordinator manually keys each invoice into our ERP (NetSuite). This takes ~6 minutes per invoice and we process ~4,000/month. Miskeying is common and duplicate payments happen 2–3 times a month.

## What we want
We want incoming invoices to be ingested automatically, key fields extracted by AI, validated against business rules, and posted to NetSuite — with a human approving anything the system is unsure about.

## Intake
- Invoices arrive at ap-invoices@acme.example as PDF attachments.
- We also want a web upload form for the AP team to drop invoices in manually.
- Each invoice must become exactly one work item with a unique ID.

## Extraction
- Extract: supplier name, supplier ID, invoice number, invoice date, line items, total amount, tax, PO number.
- If AI confidence is below 85%, do not auto-post — send to a human review queue.

## Validation rules
- The invoice total must equal the sum of line items + tax, or it is flagged.
- An invoice with the same supplier ID + invoice number seen in the last 90 days is a duplicate, not a new invoice.
- An invoice without a matching PO number cannot be auto-approved; it goes to review.
- Invoices over £10,000 always require human approval regardless of confidence.

## Approval & posting
- Approved invoices are posted to NetSuite via its REST API.
- The AP manager approves anything in the review queue.

## Reporting
- A daily dashboard of invoices processed, auto-posted vs. reviewed, and exceptions.

## Out of scope (client stated)
- Migrating the historical invoice archive.
- Phone/voice intake.
