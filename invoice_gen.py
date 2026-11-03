#!/usr/bin/env python3
"""GST invoice generator CLI.

    python invoice_gen.py sample_invoice.json -o invoice.html
    python invoice_gen.py sample_invoice.json --check   # print totals only

Input JSON keys: seller, buyer, place_of_supply_state_code, invoice, items.
Standard library only — nothing to install.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gst_invoice.build import invoice_from_dict
from gst_invoice.render import render_html
from gst_invoice.tax import compute_invoice


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="input JSON file")
    ap.add_argument("-o", "--output", default="invoice.html", help="output HTML")
    ap.add_argument("--check", action="store_true",
                    help="print computed totals, write nothing")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    invoice = invoice_from_dict(data)
    totals = compute_invoice(invoice)

    print(f"mode: {'intra-state (CGST+SGST)' if invoice.is_intra_state else 'inter-state (IGST)'}")
    print(f"subtotal ₹{totals.subtotal:,.2f} | GST ₹{totals.total_tax:,.2f} "
          f"(CGST ₹{totals.total_cgst:,.2f} + SGST ₹{totals.total_sgst:,.2f} "
          f"+ IGST ₹{totals.total_igst:,.2f})")
    print(f"round-off {totals.round_off:+.2f} | grand total ₹{totals.grand_total_rounded:,.2f}")
    if args.check:
        return 0
    Path(args.output).write_text(render_html(invoice, totals), encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
