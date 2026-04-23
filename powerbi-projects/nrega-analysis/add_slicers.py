"""
Adds comprehensive slicer panel to all 5 NREGA dashboard pages.
Slicer bar: Financial Year | Quarter | State | District | Region/Category
Run: python add_slicers.py
"""

import json, os

BASE      = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE, "NREGA-Dashboard.Report", "definition", "pages")

# ── HELPERS (same as setup script) ────────────────────────────────────────────

def col(entity, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}

def proj(field, qref, active=True):
    p = {"field": field, "queryRef": qref}
    if active: p["active"] = True
    return p

def slicer(vid, x, y, w, h, entity, prop, label, tab=0):
    """Dropdown slicer with visible header label."""
    return {
        "id": vid,
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": tab},
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [proj(col(entity, prop), f"{entity}.{prop}")]
                    }
                }
            },
            "objects": {
                "data": [{"properties": {
                    "mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}
                }}],
                "header": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FF9933'"}}}}}
                }}],
                "general": [{"properties": {
                    "orientation": {"expr": {"Literal": {"Value": "'Vertical'"}}}
                }}]
            }
        }
    }

def write_visual(page_id, visual):
    folder = os.path.join(PAGES_DIR, page_id, "visuals", visual["id"])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "visual.json")
    data = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/1.4.0/schema.json",
        "name": visual["id"],
        "position": visual["position"],
        "visual": visual["visual"]
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def delete_old_slicers(page_id, old_ids):
    """Remove old slicer visual folders."""
    for vid in old_ids:
        folder = os.path.join(PAGES_DIR, page_id, "visuals", vid)
        if os.path.exists(folder):
            import shutil
            shutil.rmtree(folder)

# ── SLICER LAYOUT ─────────────────────────────────────────────────────────────
# Bottom slicer bar: y=625, h=70, 5 slicers across 1280px
# x positions:  10 | 266 | 522 | 778 | 1034
# widths:       246   246   246   246   236

SL_Y  = 627
SL_H  = 68
SL_W  = 240
GAP   = 10
POSITIONS = [
    GAP,
    GAP + SL_W + GAP,
    GAP + 2*(SL_W + GAP),
    GAP + 3*(SL_W + GAP),
    GAP + 4*(SL_W + GAP),
]

# ── PAGE 1 — Executive Summary ─────────────────────────────────────────────────
P1 = "p1execsummary0001"
delete_old_slicers(P1, ["p1sl"])

p1_slicers = [
    slicer("p1sl_fy",  POSITIONS[0], SL_Y, SL_W, SL_H, "dim_date",      "financial_year",    "Financial Year", tab=20),
    slicer("p1sl_fq",  POSITIONS[1], SL_Y, SL_W, SL_H, "dim_date",      "financial_quarter", "Quarter",        tab=21),
    slicer("p1sl_rg",  POSITIONS[2], SL_Y, SL_W, SL_H, "dim_geography", "region",            "Region",         tab=22),
    slicer("p1sl_st",  POSITIONS[3], SL_Y, SL_W, SL_H, "dim_geography", "state_name",        "State",          tab=23),
    slicer("p1sl_mn",  POSITIONS[4], SL_Y, SL_W, SL_H, "dim_date",      "month_short",       "Month",          tab=24),
]
for s in p1_slicers:
    write_visual(P1, s)
print(f"  Page 1 — {len(p1_slicers)} slicers added")

# ── PAGE 2 — Employment & Demand ──────────────────────────────────────────────
P2 = "p2employment00002"
delete_old_slicers(P2, ["p2sl1", "p2sl2"])

p2_slicers = [
    slicer("p2sl_fy",  POSITIONS[0], SL_Y, SL_W, SL_H, "dim_date",      "financial_year",    "Financial Year", tab=20),
    slicer("p2sl_fq",  POSITIONS[1], SL_Y, SL_W, SL_H, "dim_date",      "financial_quarter", "Quarter",        tab=21),
    slicer("p2sl_st",  POSITIONS[2], SL_Y, SL_W, SL_H, "dim_geography", "state_name",        "State",          tab=22),
    slicer("p2sl_dt",  POSITIONS[3], SL_Y, SL_W, SL_H, "dim_geography", "district_name",     "District",       tab=23),
    slicer("p2sl_rg",  POSITIONS[4], SL_Y, SL_W, SL_H, "dim_geography", "region",            "Region",         tab=24),
]
for s in p2_slicers:
    write_visual(P2, s)
print(f"  Page 2 — {len(p2_slicers)} slicers added")

# ── PAGE 3 — Social Equity ────────────────────────────────────────────────────
P3 = "p3socialequity003"
delete_old_slicers(P3, ["p3sl1", "p3sl2"])

p3_slicers = [
    slicer("p3sl_fy",  POSITIONS[0], SL_Y, SL_W, SL_H, "dim_date",      "financial_year",    "Financial Year", tab=20),
    slicer("p3sl_fq",  POSITIONS[1], SL_Y, SL_W, SL_H, "dim_date",      "financial_quarter", "Quarter",        tab=21),
    slicer("p3sl_st",  POSITIONS[2], SL_Y, SL_W, SL_H, "dim_geography", "state_name",        "State",          tab=22),
    slicer("p3sl_dt",  POSITIONS[3], SL_Y, SL_W, SL_H, "dim_geography", "district_name",     "District",       tab=23),
    slicer("p3sl_rg",  POSITIONS[4], SL_Y, SL_W, SL_H, "dim_geography", "region",            "Region",         tab=24),
]
for s in p3_slicers:
    write_visual(P3, s)
print(f"  Page 3 — {len(p3_slicers)} slicers added")

# ── PAGE 4 — Wages & Payment ──────────────────────────────────────────────────
P4 = "p4wagespayment004"
delete_old_slicers(P4, ["p4sl1", "p4sl2"])

p4_slicers = [
    slicer("p4sl_fy",  POSITIONS[0], SL_Y, SL_W, SL_H, "dim_date",      "financial_year",    "Financial Year", tab=20),
    slicer("p4sl_fq",  POSITIONS[1], SL_Y, SL_W, SL_H, "dim_date",      "financial_quarter", "Quarter",        tab=21),
    slicer("p4sl_st",  POSITIONS[2], SL_Y, SL_W, SL_H, "dim_geography", "state_name",        "State",          tab=22),
    slicer("p4sl_dt",  POSITIONS[3], SL_Y, SL_W, SL_H, "dim_geography", "district_name",     "District",       tab=23),
    slicer("p4sl_mn",  POSITIONS[4], SL_Y, SL_W, SL_H, "dim_date",      "month_short",       "Month",          tab=24),
]
for s in p4_slicers:
    write_visual(P4, s)
print(f"  Page 4 — {len(p4_slicers)} slicers added")

# ── PAGE 5 — Works & Assets ───────────────────────────────────────────────────
P5 = "p5worksassets0005"
delete_old_slicers(P5, ["p5sl1", "p5sl2"])

p5_slicers = [
    slicer("p5sl_fy",  POSITIONS[0], SL_Y, SL_W, SL_H, "dim_date",      "financial_year",    "Financial Year",  tab=20),
    slicer("p5sl_fq",  POSITIONS[1], SL_Y, SL_W, SL_H, "dim_date",      "financial_quarter", "Quarter",         tab=21),
    slicer("p5sl_st",  POSITIONS[2], SL_Y, SL_W, SL_H, "dim_geography", "state_name",        "State",           tab=22),
    slicer("p5sl_dt",  POSITIONS[3], SL_Y, SL_W, SL_H, "dim_geography", "district_name",     "District",        tab=23),
    slicer("p5sl_ct",  POSITIONS[4], SL_Y, SL_W, SL_H, "dim_work_category", "category_name", "Work Category",   tab=24),
]
for s in p5_slicers:
    write_visual(P5, s)
print(f"  Page 5 — {len(p5_slicers)} slicers added")

print("\nAll slicers updated. Reload NREGA-Dashboard.pbip in Power BI Desktop.")
