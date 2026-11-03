import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gst_invoice.build import invoice_from_dict
from gst_invoice.numbering import fy_label
from gst_invoice.tax import compute_invoice, compute_line, extract_base_from_inclusive
from gst_invoice.models import LineItem
from gst_invoice.words import amount_in_words

import json
SAMPLE = json.loads((Path(__file__).resolve().parent.parent
                     / "sample_invoice.json").read_text(encoding="utf-8"))


def D(x):
    return Decimal(str(x))


class TestSampleInvoice(unittest.TestCase):
    """Same basket as the independently verified v1 demo:
    subtotal 13,924.00, GST 1,597.77, grand 15,522.00 after +0.23 round-off."""

    def setUp(self):
        self.totals = compute_invoice(invoice_from_dict(SAMPLE))

    def test_totals(self):
        t = self.totals
        self.assertEqual(t.subtotal, D("13924.00"))
        self.assertEqual(t.total_tax, D("1597.77"))
        self.assertEqual(t.grand_total, D("15521.77"))
        self.assertEqual(t.round_off, D("0.23"))
        self.assertEqual(t.grand_total_rounded, D("15522"))

    def test_rate_buckets(self):
        by = {str(s.gst_percent): s for s in self.totals.by_rate}
        self.assertEqual(by["5"].cgst + by["5"].sgst, D("321.75"))
        self.assertEqual(by["12"].cgst + by["12"].sgst, D("144.00"))
        self.assertEqual(by["18"].cgst + by["18"].sgst, D("1132.02"))

    def test_split_always_sums_exactly(self):
        t = self.totals
        self.assertEqual(t.total_cgst + t.total_sgst + t.total_igst, t.total_tax)
        self.assertEqual(t.total_igst, D("0"))

    def test_inter_state_same_grand_total(self):
        data = json.loads(json.dumps(SAMPLE))
        data["place_of_supply_state_code"] = "27"
        data["buyer"]["state_code"] = "27"
        data["buyer"]["gstin"] = "27PQRST6789K1Z3"
        totals = compute_invoice(invoice_from_dict(data))
        self.assertEqual(totals.total_igst, D("1597.77"))
        self.assertEqual(totals.total_cgst, D("0"))
        self.assertEqual(totals.grand_total_rounded, D("15522"))


class TestEdgeCases(unittest.TestCase):
    def test_odd_paisa_split(self):
        line = compute_line(LineItem("X", "0000", D("1"), D("101"), D("5")), True)
        # tax = 5.05 -> CGST 2.53, SGST 2.52; split sums exactly
        self.assertEqual(line.tax, D("5.05"))
        self.assertEqual(line.cgst + line.sgst, D("5.05"))

    def test_inclusive_reverse(self):
        self.assertEqual(extract_base_from_inclusive(D("11800"), D("18")), D("10000.00"))

    def test_discount(self):
        line = compute_line(
            LineItem("Y", "0000", D("2"), D("500"), D("18"), D("10")), False)
        self.assertEqual(line.taxable, D("900.00"))
        self.assertEqual(line.igst, D("162.00"))

    def test_fy_label(self):
        self.assertEqual(fy_label(date(2026, 11, 2)), "2026-27")
        self.assertEqual(fy_label(date(2027, 2, 1)), "2026-27")
        self.assertEqual(fy_label(date(2027, 4, 1)), "2027-28")

    def test_words(self):
        self.assertEqual(amount_in_words(D("15522")),
                         "Rupees Fifteen Thousand Five Hundred Twenty Two Only")
        self.assertEqual(amount_in_words(D("100000")),
                         "Rupees One Lakh Only")
        self.assertEqual(amount_in_words(D("12345678")),
                         "Rupees One Crore Twenty Three Lakh Forty Five "
                         "Thousand Six Hundred Seventy Eight Only")


if __name__ == "__main__":
    unittest.main()
