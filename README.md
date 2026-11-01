# GST Invoice Generator

A command-line Python tool for small shops and traders: feed it your items,
and it generates a **professional, print-ready GST invoice (HTML)** with all
tax maths done automatically — no spreadsheet formulas, no calculation
mistakes, no installs (Python standard library only).

## What it does

- Seller/buyer details, invoice number, date and due date on the invoice
- Per-item rows: name, HSN code, quantity, rate, GST % — with line-wise
  taxable value and tax
- **Automatic GST logic:** comparing seller and buyer state codes decides
  **CGST + SGST** (same state, tax split in half) or **IGST** (other state)
- **Tax summary grouped by GST rate** (e.g. 5% / 12% / 18%)
- Subtotal, total GST, round-off and **Grand Total**
- **Amount in words** in the Indian numbering system (Lakh/Crore), e.g.
  "Rupees Fifteen Thousand Five Hundred Twenty Two Only"
- Money maths with `Decimal` and half-up rounding — no float errors

## How to run

No installation needed — just Python 3.8+.

```bash
# JSON input (the whole invoice in one file)
python3 invoice_gen.py --input sample_invoice.json --output sample_invoice.html

# CSV input (items in CSV, shop/customer details in a meta JSON file)
python3 invoice_gen.py --input sample_items.csv --meta sample_meta.json --output sample_invoice_from_csv.html
```

Open the generated HTML in a browser → Print (Ctrl+P) → save as PDF or print.

## Real output from the sample data

```text
Invoice ready: sample_invoice.html
  Subtotal ₹13,924.00 + GST ₹1,597.77 = Grand Total ₹15,522.00 (CGST/SGST)
  In words: Rupees Fifteen Thousand Five Hundred Twenty Two Only
```

Tax summary of the sample invoice: 5% → ₹321.75 · 12% → ₹144.00 · 18% → ₹1,132.02
(totals independently re-verified outside the tool — exact match).

## Files

| File | What it is |
|---|---|
| `invoice_gen.py` | The tool (standard library only, ~13 KB) |
| `sample_invoice.json` | Sample input — JSON mode |
| `sample_items.csv` + `sample_meta.json` | Sample input — CSV mode |
| `sample_invoice.html` | Generated invoice (JSON mode) |
| `sample_invoice_from_csv.html` | Generated invoice (CSV mode) |

## Tech used

Python 3 (standard library only) · `argparse` · `csv` · `json` · `decimal` · HTML output

## Hire me

Want a billing/invoice tool or another repetitive Excel/data task automated
for your business? **Demo first — on YOUR sample — before you pay anything.**

- Fiverr gig (from $15): https://www.fiverr.com/lenevo509/build-a-python-web-scraper-or-automation-script-for-you
- LinkedIn: https://www.linkedin.com/in/abhishek-phukan-a220b9448/

*Built by Abhishek Phukan — Python Automation Developer, Digboi, Assam, India.*
