# customer_pricing.py  – stand-alone price breakdown + PDF report
# --------------------------------------------------------------
# Edit MATERIALS, LABOR_HOURS, LABOR_RATE at the top, then run.
# A PDF called customer_pricing.pdf will be created next to this file.

import pathlib
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# ───────────────────────────────────────────────────────────────
#  1. INPUTS  ➜  edit these
# ───────────────────────────────────────────────────────────────
MATERIALS = [{"name": "4/0 THHN Copper Roll", "qty": 1, "unit_cost": 1200}, {"name": "2 in. Rigid Conduit 10 ft", "qty": 50, "unit_cost": 40}
    # Example rows – replace or append your own:
    # {"name": "3⁄4-in EMT Conduit", "qty": 10, "unit_cost": 15.50},
    # {"name": "4-SQ Box",         "qty": 25, "unit_cost":  3.20},
]

LABOR_HOURS = 20          # e.g. 8
LABOR_RATE  = 80.0       # $/hr

# Cost parameters
TAX_RATE        = 0.0913
OVERHEAD_RATE   = 0.6666     # 66.66 %
PROFIT_MARGIN   = 0.23
COMMISSION_RATE = 0.20
# ───────────────────────────────────────────────────────────────


def compute_final_price(material_cost, labor_cost,
                        tax_rate=TAX_RATE,
                        overhead_rate=OVERHEAD_RATE,
                        profit_margin=PROFIT_MARGIN,
                        commission_rate=COMMISSION_RATE,
                        tol=1e-6, max_iter=1000):
    """Return (final_price, breakdown_dict) under recursive commission rules."""
    taxed_material = material_cost * (1 + tax_rate)
    price = taxed_material + labor_cost  # initial guess
    for _ in range(max_iter):
        profit      = price * profit_margin
        commission  = profit * commission_rate
        total_labor = labor_cost + commission
        base_cost   = taxed_material + total_labor
        overhead    = base_cost * overhead_rate
        total_cost  = base_cost + overhead
        new_price   = total_cost / (1 - profit_margin)
        if abs(new_price - price) < tol:
            price = new_price
            break
        price = new_price
    else:
        raise RuntimeError("Convergence failed")

    # final breakdown
    profit      = price * profit_margin
    commission  = profit * commission_rate
    total_labor = labor_cost + commission
    base_cost   = taxed_material + total_labor
    overhead    = base_cost * overhead_rate
    total_cost  = base_cost + overhead

    breakdown = {
        "Material Raw"   : round(material_cost, 2),
        "Material Taxed" : round(taxed_material, 2),
        "Labor Base"     : round(labor_cost, 2),
        "Commission"     : round(commission, 2),
        "Labor Total"    : round(total_labor, 2),
        "Overhead"       : round(overhead, 2),
        "Total Cost"     : round(total_cost, 2),
        "Profit"         : round(profit, 2),
        "Final Price"    : round(price, 2),
    }
    return round(price, 2), breakdown


def main():
    if not MATERIALS:
        raise ValueError("⚠️  MATERIALS list is empty — add items, then rerun.")

    # 2. line totals
    for itm in MATERIALS:
        itm["line_total"] = itm["qty"] * itm["unit_cost"]

    raw_total  = sum(i["line_total"] for i in MATERIALS)
    labor_base = LABOR_HOURS * LABOR_RATE
    final_price, breakdown = compute_final_price(raw_total, labor_base)

    # 3. console preview
    print("\nMaterials:")
    for itm in MATERIALS:
        print(f"  {itm['qty']:>3} × {itm['name']:<25}  @ ${itm['unit_cost']:>7.2f}"
              f" = ${itm['line_total']:>8.2f}")
    print("\nBreakdown:")
    for k, v in breakdown.items():
        print(f"  {k:<15}: ${v:>10,.2f}")

    # 4. build PDF with nicer table formatting
    pdf_path = pathlib.Path(__file__).with_name("customer_pricing.pdf")
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=1*inch, bottomMargin=0.75*inch)
    elements = []

    # Title
    elements.append(Table([["Customer Pricing Breakdown"]],
                          style=[('FONTSIZE', (0,0), (-1,-1), 16),
                                 ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                                 ('BOTTOMPADDING', (0,0), (-1,-1), 12)]))

    # Materials table
    mat_rows = [["Qty", "Item", "Line $"]]
    for itm in MATERIALS:
        mat_rows.append([itm['qty'],
                         itm['name'],
                         f"${itm['line_total']:,.2f}"])
    materials_tbl = Table(mat_rows, colWidths=[0.6*inch, 3.5*inch, 1.2*inch])
    materials_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('ALIGN', (-1,1), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,1), (0,-1), 'CENTER'),
        ('LEFTPADDING', (1,1), (1,-1), 4),
    ]))
    elements.append(materials_tbl)
    elements.append(Table([[" "]]))  # spacer

    # Breakdown table
    br_rows = [[k, f"${v:,.2f}"] for k, v in breakdown.items()]
    br_tbl = Table(br_rows, colWidths=[2.5*inch, 1.2*inch])
    br_tbl.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('LEFTPADDING', (0,0), (0,-1), 4),
    ]))
    elements.append(br_tbl)

    doc.build(elements)
    print(f"\nPDF saved to: {pdf_path}")


if __name__ == "__main__":
    main()
