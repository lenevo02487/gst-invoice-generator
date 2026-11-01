#!/usr/bin/env python3
"""
GST Invoice Generator — chhoti dukaan ke liye professional tax invoice.

Input : JSON (poori invoice) ya CSV (items) + --meta JSON (shop/customer details)
Output: ek saaf, print-ready HTML invoice — GST hisaab ke saath:
        subtotal, CGST/SGST (same state) ya IGST (dusra state),
        tax summary per GST rate, grand total, amount in words (Indian system).

Usage:
    python3 invoice_gen.py --input sample_invoice.json --output invoice.html
    python3 invoice_gen.py --input sample_items.csv --meta sample_meta.json --output invoice.html

Sirf Python standard library — koi install nahi chahiye. Python 3.8+.
"""

import argparse
import csv
import html
import json
import sys
from decimal import Decimal, ROUND_HALF_UP

D = Decimal
CENT = D("0.01")


def money(x):
    """2-decimal rounding, banker's nahi — half-up (dukaan wala hisaab)."""
    return D(x).quantize(CENT, rounding=ROUND_HALF_UP)


def fmt(x):
    """Indian number format: 1,23,456.78"""
    x = money(x)
    neg = x < 0
    x = abs(x)
    rupees = int(x)
    paise = int((x - rupees) * 100)
    s = str(rupees)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    out = f"{s}.{paise:02d}"
    return ("-" if neg else "") + out


# ---------- Amount in words (Indian system: crore / lakh / thousand) ----------
ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
        "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
        "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
        "Eighty", "Ninety"]


def _two(n):
    if n < 20:
        return ONES[n]
    t, o = divmod(n, 10)
    return (TENS[t] + (" " + ONES[o] if o else "")).strip()


def _three(n):
    h, rest = divmod(n, 100)
    out = ""
    if h:
        out = ONES[h] + " Hundred"
    if rest:
        out = (out + " " + _two(rest)).strip()
    return out


def amount_in_words(amount):
    """Decimal rupees -> 'Rupees One Thousand Two Hundred Thirty Four and Paise Fifty Only'"""
    amount = money(amount)
    rupees = int(amount)
    paise = int((amount - rupees) * 100)
    if rupees == 0 and paise == 0:
        return "Rupees Zero Only"
    parts = []
    crore, rem = divmod(rupees, 10_000_000)
    lakh, rem = divmod(rem, 100_000)
    thou, rest = divmod(rem, 1_000)
    if crore:
        parts.append(_three(crore) + " Crore")
    if lakh:
        parts.append(_two(lakh) + " Lakh")
    if thou:
        parts.append(_two(thou) + " Thousand")
    if rest:
        parts.append(_three(rest))
    words = "Rupees " + " ".join(p for p in parts if p)
    if paise:
        words += f" and Paise {_two(paise)}"
    return words + " Only"


# ---------- Input loading ----------
def load_input(args):
    if args.input.lower().endswith(".json"):
        with open(args.input, encoding="utf-8") as f:
            return json.load(f)
    if args.input.lower().endswith(".csv"):
        if not args.meta:
            sys.exit("CSV input ke liye --meta <meta.json> zaroori hai "
                     "(shop/customer/invoice details usi me rahenge).")
        with open(args.meta, encoding="utf-8") as f:
            data = json.load(f)
        items = []
        with open(args.input, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                items.append({
                    "name": row["name"],
                    "hsn": row.get("hsn", ""),
                    "qty": row["qty"],
                    "rate": row["rate"],
                    "gst_percent": row["gst_percent"],
                })
        data["items"] = items
        return data
    sys.exit("Input sirf .json ya .csv ho sakta hai.")


# ---------- GST calculation ----------
def compute(data):
    shop_state = str(data["shop"].get("state_code", "")).strip()
    supply_state = str(data.get("place_of_supply_state_code",
                               data["customer"].get("state_code", ""))).strip()
    if not shop_state or not supply_state:
        sys.exit("state_code zaroori hai (shop + customer/place_of_supply) — "
                 "CGST/SGST ya IGST isiliye tay hota hai.")
    intra = shop_state == supply_state

    lines = []
    tax_groups = {}  # gst_percent -> {taxable, cgst, sgst, igst}
    subtotal = D("0")
    total_tax = D("0")

    for it in data["items"]:
        qty = D(str(it["qty"]))
        rate = D(str(it["rate"]))
        gst = D(str(it["gst_percent"]))
        taxable = money(qty * rate)
        tax = money(taxable * gst / 100)
        if intra:
            half = money(tax / 2)
            cgst = sgst = half
            # odd-paisa case: dusra half bacha hua, taaki kul tax exact rahe
            sgst = tax - cgst
            igst = D("0")
        else:
            cgst = sgst = D("0")
            igst = tax
        line_total = taxable + tax
        lines.append({
            "name": it["name"], "hsn": it.get("hsn", ""),
            "qty": qty, "rate": rate, "gst": gst,
            "taxable": taxable, "cgst": cgst, "sgst": sgst,
            "igst": igst, "total": line_total,
        })
        g = tax_groups.setdefault(gst, {"taxable": D("0"), "cgst": D("0"),
                                        "sgst": D("0"), "igst": D("0"),
                                        "tax": D("0")})
        g["taxable"] += taxable
        g["cgst"] += cgst
        g["sgst"] += sgst
        g["igst"] += igst
        g["tax"] += tax
        subtotal += taxable
        total_tax += tax

    grand = subtotal + total_tax
    grand_rounded = grand.quantize(D("1"), rounding=ROUND_HALF_UP)
    round_off = grand_rounded - grand

    return {
        "intra": intra, "lines": lines, "tax_groups": tax_groups,
        "subtotal": subtotal, "total_tax": total_tax,
        "grand": grand, "grand_rounded": grand_rounded,
        "round_off": round_off,
        "words": amount_in_words(grand_rounded),
    }


# ---------- HTML rendering (print-ready) ----------
def render_html(data, calc):
    e = html.escape
    shop = data["shop"]
    cust = data["customer"]
    inv = data["invoice"]
    intra = calc["intra"]

    item_rows = ""
    for i, ln in enumerate(calc["lines"], 1):
        if intra:
            tax_cell = (f"CGST ₹{fmt(ln['cgst'])}<br>SGST ₹{fmt(ln['sgst'])}")
        else:
            tax_cell = f"IGST ₹{fmt(ln['igst'])}"
        item_rows += f"""<tr>
          <td>{i}</td><td>{e(str(ln['name']))}<br><small>HSN: {e(str(ln['hsn']))}</small></td>
          <td class="r">{ln['qty']}</td><td class="r">₹{fmt(ln['rate'])}</td>
          <td class="r">₹{fmt(ln['taxable'])}</td>
          <td class="r">{ln['gst']}%</td><td class="r">{tax_cell}</td>
          <td class="r"><strong>₹{fmt(ln['total'])}</strong></td></tr>\n"""

    group_rows = ""
    for gst in sorted(calc["tax_groups"]):
        g = calc["tax_groups"][gst]
        if intra:
            half = gst / 2
            group_rows += (f"<tr><td>{gst}% (CGST {half}% + SGST {half}%)</td>"
                           f"<td class='r'>₹{fmt(g['taxable'])}</td>"
                           f"<td class='r'>₹{fmt(g['cgst'])}</td>"
                           f"<td class='r'>₹{fmt(g['sgst'])}</td>"
                           f"<td class='r'>₹{fmt(g['tax'])}</td></tr>\n")
        else:
            group_rows += (f"<tr><td>{gst}% (IGST)</td>"
                           f"<td class='r'>₹{fmt(g['taxable'])}</td>"
                           f"<td class='r' colspan='2'>₹{fmt(g['igst'])}</td>"
                           f"<td class='r'>₹{fmt(g['tax'])}</td></tr>\n")

    roundoff_row = ""
    if calc["round_off"] != 0:
        roundoff_row = (f"<tr><td colspan='7'>Round off</td>"
                        f"<td class='r'>₹{fmt(calc['round_off'])}</td></tr>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Invoice {e(str(inv['number']))} — {e(str(shop['name']))}</title>
<style>
  @page {{ margin: 14mm; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: Georgia, 'Times New Roman', serif; color:#1c2420;
         max-width: 800px; margin: 24px auto; padding: 0 20px; }}
  .head {{ display:flex; justify-content:space-between; border-bottom:3px solid #173f2c;
           padding-bottom:12px; margin-bottom:14px; }}
  .head h1 {{ font-size:26px; color:#173f2c; }}
  .head .meta {{ text-align:right; font-size:13px; color:#44534b; }}
  h2.title {{ text-align:center; letter-spacing:2px; font-size:15px;
              text-transform:uppercase; margin:6px 0 14px; color:#173f2c; }}
  .parties {{ display:flex; gap:24px; margin-bottom:16px; font-size:14px; }}
  .parties > div {{ flex:1; border:1px solid #cdd6cf; padding:10px 12px; }}
  .parties h3 {{ font-size:12px; text-transform:uppercase; letter-spacing:1px;
                 color:#718076; margin-bottom:4px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13.5px; margin-bottom:16px; }}
  th {{ background:#173f2c; color:#fff; text-align:left; padding:7px 8px; font-weight:600; }}
  td {{ border-bottom:1px solid #dde3de; padding:7px 8px; vertical-align:top; }}
  td.r, th.r {{ text-align:right; }}
  .totals td {{ border-bottom:none; font-size:14.5px; }}
  .totals .grand td {{ border-top:2.5px solid #173f2c; font-size:17px; font-weight:bold; }}
  .words {{ background:#eef4ef; padding:10px 12px; font-size:14px; margin-bottom:16px; }}
  .foot {{ display:flex; justify-content:space-between; align-items:flex-end;
           margin-top:28px; font-size:13px; color:#44534b; }}
  .sign {{ text-align:center; }}
  .sign .line {{ border-top:1px solid #1c2420; margin-top:44px; padding-top:5px; }}
  @media print {{ body {{ margin:0; }} }}
</style>
</head>
<body>
  <div class="head">
    <div>
      <h1>{e(str(shop['name']))}</h1>
      <p>{e(str(shop.get('address','')))}<br>
      Phone: {e(str(shop.get('phone','')))} · GSTIN: <strong>{e(str(shop.get('gstin','')))}</strong></p>
    </div>
    <div class="meta">
      Invoice No: <strong>{e(str(inv['number']))}</strong><br>
      Date: {e(str(inv['date']))}<br>
      Due: {e(str(inv.get('due_date','')))}
    </div>
  </div>

  <h2 class="title">Tax Invoice</h2>

  <div class="parties">
    <div>
      <h3>Bill To</h3>
      <strong>{e(str(cust['name']))}</strong><br>
      {e(str(cust.get('address','')))}<br>
      GSTIN: {e(str(cust.get('gstin','—')))}<br>
      Place of Supply: {e(str(data.get('place_of_supply','')))} (State Code: {e(str(data.get('place_of_supply_state_code', cust.get('state_code',''))))})
    </div>
    <div>
      <h3>Tax Type</h3>
      {"Intra-state supply — CGST + SGST lagu" if intra else "Inter-state supply — IGST lagu"}
    </div>
  </div>

  <table>
    <tr><th>#</th><th>Item</th><th class="r">Qty</th><th class="r">Rate</th>
        <th class="r">Taxable</th><th class="r">GST</th><th class="r">Tax</th><th class="r">Amount</th></tr>
{item_rows}  </table>

  <h3 style="margin-bottom:6px; color:#173f2c;">Tax Summary</h3>
  <table>
    <tr><th>GST Rate</th><th class="r">Taxable Value</th><th class="r">CGST</th>
        <th class="r">SGST / —</th><th class="r">Total Tax</th></tr>
{group_rows}  </table>

  <table class="totals">
    <tr><td colspan="7">Subtotal (taxable value)</td><td class="r">₹{fmt(calc['subtotal'])}</td></tr>
    <tr><td colspan="7">Total GST</td><td class="r">₹{fmt(calc['total_tax'])}</td></tr>
{roundoff_row}    <tr class="grand"><td colspan="7">Grand Total</td><td class="r">₹{fmt(calc['grand_rounded'])}</td></tr>
  </table>

  <div class="words"><strong>Amount in words:</strong> {e(calc['words'])}</div>

  <div class="foot">
    <p>Thank you for your business!<br>Payment due by {e(str(inv.get('due_date','')))}.</p>
    <div class="sign">
      <p>For {e(str(shop['name']))}</p>
      <div class="line">Authorised Signatory</div>
    </div>
  </div>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="GST Invoice Generator")
    ap.add_argument("--input", required=True, help="input .json ya .csv file")
    ap.add_argument("--meta", help="CSV mode ke liye meta .json (shop/customer/invoice)")
    ap.add_argument("--output", required=True, help="output .html file")
    args = ap.parse_args()

    data = load_input(args)
    calc = compute(data)
    out = render_html(data, calc)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Invoice ready: {args.output}")
    print(f"  Subtotal ₹{fmt(calc['subtotal'])} + GST ₹{fmt(calc['total_tax'])}"
          f" = Grand Total ₹{fmt(calc['grand_rounded'])}"
          f" ({'CGST/SGST' if calc['intra'] else 'IGST'})")
    print(f"  In words: {calc['words']}")


if __name__ == "__main__":
    main()
