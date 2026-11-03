# GST Invoice Generator — Decimal-Exact, Stdlib-Only

A command-line GST invoice generator in pure Python (standard library
only — nothing to install). Feed it a JSON invoice, get a print-ready
HTML tax invoice with correct CGST/SGST or IGST, per-rate tax summary,
round-off line and amount in words (Indian numbering system).

## What it does

- **Per-line-item tax** at each item's own GST rate — never one rate on
  the invoice total
- **CGST/SGST vs IGST decided by one rule:** seller state vs place of
  supply. Same state → tax split half/half; different → full IGST
- **Exact split on odd paise:** CGST is rounded, SGST = tax − CGST, so
  CGST + SGST always equals the line GST to the paisa
- All money in `Decimal`, rounded to the paisa with `ROUND_HALF_UP`
- Grand total rounded to the nearest rupee with an explicit round-off line
- GSTIN format + state-prefix validation, FY-aware (April–March)
  sequential invoice numbering helper, tax-inclusive price reverse
  calculator (`extract_base_from_inclusive`)

## Run it

```bash
python invoice_gen.py sample_invoice.json -o invoice.html
python invoice_gen.py sample_invoice.json --check   # totals only
python -m unittest discover -s tests                # 9 tests
```

## Sample run (actual output)

```
mode: intra-state (CGST+SGST)
subtotal ₹13,924.00 | GST ₹1,597.77 (CGST ₹798.89 + SGST ₹798.88 + IGST ₹0.00)
round-off +0.23 | grand total ₹15,522.00
```

The same basket sent inter-state produces IGST ₹1,597.77 and the same
₹15,522.00 grand total — both cases are covered by tests, along with
discount lines, odd-paisa splits and amount-in-words
("Rupees Fifteen Thousand Five Hundred Twenty Two Only").

## Layout

```
gst_invoice/
  models.py     Party / LineItem / Invoice dataclasses + validation
  tax.py        per-line computation, rate summaries, round-off
  numbering.py  financial-year invoice series (JSON state file)
  words.py      amount in words — crore / lakh / thousand
  build.py      JSON dict -> Invoice (input boundary)
  render.py     print-ready HTML invoice
invoice_gen.py  CLI
```

## Honest scope

This generates correct invoice documents and arithmetic. It is not
e-invoicing (IRN), GSTR filing, or tax advice — rates come from your
input, so confirm each item's rate for your HSN/SAC before issuing.

## Want one for your business?

Send me your shop details and one sample bill — I'll generate a demo
invoice with your own data first, free. Judge the output, then decide.
— Abhishek
