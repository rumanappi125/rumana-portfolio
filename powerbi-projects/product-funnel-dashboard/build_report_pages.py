"""
Generates all 4 Power BI report page JSON files for the Product Funnel Dashboard.
Run: python build_report_pages.py
Output: writes page.json files into the .Report/definition/pages/ folder
"""

import json, os

REPORT_DIR = "Product-Funnel-Dashboard.Report/definition"
PAGES_DIR  = os.path.join(REPORT_DIR, "pages")

# ── HELPERS ───────────────────────────────────────────────────────────────────

def measure(name):
    return {
        "Measure": {
            "Expression": {"SourceRef": {"Entity": "_Measures"}},
            "Property": name
        }
    }

def column(entity, prop):
    return {
        "Column": {
            "Expression": {"SourceRef": {"Entity": entity}},
            "Property": prop
        }
    }

def col_agg(entity, prop, fn=5):
    """fn: 0=Sum, 1=Avg, 2=Min, 3=Max, 4=Count, 5=CountNonNull"""
    return {
        "Aggregation": {
            "Expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Entity": entity}},
                    "Property": prop
                }
            },
            "Function": fn
        }
    }

def projection(field, qref, active=True):
    p = {"field": field, "queryRef": qref}
    if active:
        p["active"] = True
    return p

def card(vid, x, y, w, h, measure_name, tab=0):
    return {
        "id": vid,
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": tab},
        "visual": {
            "visualType": "card",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            projection(measure(measure_name), f"_Measures.{measure_name}")
                        ]
                    }
                }
            },
            "objects": {
                "labels": [{"properties": {"fontSize": {"expr": {"Literal": {"Value": "11D"}}}}}]
            }
        }
    }

def col_chart(vid, x, y, w, h, cat_entity, cat_prop, y_measures, tab=0):
    y_proj = []
    for mn in y_measures:
        y_proj.append(projection(measure(mn), f"_Measures.{mn}"))
    return {
        "id": vid,
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": tab},
        "visual": {
            "visualType": "columnChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            projection(column(cat_entity, cat_prop), f"{cat_entity}.{cat_prop}")
                        ]
                    },
                    "Y": {"projections": y_proj}
                }
            }
        }
    }

def bar_chart(vid, x, y, w, h, cat_entity, cat_prop, y_measures, tab=0):
    v = col_chart(vid, x, y, w, h, cat_entity, cat_prop, y_measures, tab)
    v["visual"]["visualType"] = "barChart"
    return v

def line_chart(vid, x, y, w, h, cat_entity, cat_prop, y_measures, tab=0):
    v = col_chart(vid, x, y, w, h, cat_entity, cat_prop, y_measures, tab)
    v["visual"]["visualType"] = "lineChart"
    return v

def donut_chart(vid, x, y, w, h, cat_entity, cat_prop, y_measure, tab=0):
    return {
        "id": vid,
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": tab},
        "visual": {
            "visualType": "donutChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            projection(column(cat_entity, cat_prop), f"{cat_entity}.{cat_prop}")
                        ]
                    },
                    "Y": {
                        "projections": [
                            projection(measure(y_measure), f"_Measures.{y_measure}")
                        ]
                    }
                }
            }
        }
    }

def funnel_chart(vid, x, y, w, h, cat_entity, cat_prop, tab=0):
    return {
        "id": vid,
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": tab},
        "visual": {
            "visualType": "funnel",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            projection(column(cat_entity, cat_prop), f"{cat_entity}.{cat_prop}")
                        ]
                    },
                    "Y": {
                        "projections": [
                            projection(
                                col_agg(cat_entity, "user_id", 5),
                                f"Count({cat_entity}.user_id)"
                            )
                        ]
                    }
                }
            }
        }
    }

def slicer(vid, x, y, w, h, entity, prop, tab=0):
    return {
        "id": vid,
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": tab},
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            projection(column(entity, prop), f"{entity}.{prop}")
                        ]
                    }
                }
            },
            "objects": {
                "general": [{"properties": {"orientation": {"expr": {"Literal": {"Value": "'Horizontal'"}}}}}]
            }
        }
    }

def matrix(vid, x, y, w, h, row_entity, row_prop, col_entity, col_prop, val_measures, tab=0):
    val_proj = [projection(measure(m), f"_Measures.{m}") for m in val_measures]
    return {
        "id": vid,
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": tab},
        "visual": {
            "visualType": "matrix",
            "query": {
                "queryState": {
                    "Rows": {
                        "projections": [
                            projection(column(row_entity, row_prop), f"{row_entity}.{row_prop}")
                        ]
                    },
                    "Columns": {
                        "projections": [
                            projection(column(col_entity, col_prop), f"{col_entity}.{col_prop}")
                        ]
                    },
                    "Values": {"projections": val_proj}
                }
            }
        }
    }

def make_page(page_id, display_name):
    """Page metadata only — visuals go in separate visual.json files."""
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": page_id,
        "displayName": display_name,
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280
    }

def make_visual(visual_def):
    """Wrap a visual container definition for writing as its own visual.json file."""
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/1.4.0/schema.json",
        "name": visual_def["id"],
        "position": visual_def["position"],
        "visual": visual_def["visual"]
    }


# ── PAGE 1: FUNNEL ANALYSIS ───────────────────────────────────────────────────
P1_ID = "87dab80ddd51d681590e"

page1_visuals = [
    # Row 1 — Stage user counts
    card("p1_c1",  20,  20, 230, 90, "Signup Users",           tab=0),
    card("p1_c2", 260,  20, 230, 90, "Explore Users",          tab=1),
    card("p1_c3", 500,  20, 230, 90, "Checkout Users",         tab=2),
    card("p1_c4", 740,  20, 230, 90, "Payment Users",          tab=3),
    card("p1_c5", 980,  20, 280, 90, "Overall Conversion Rate",tab=4),

    # Row 2 — Stage conversion rates
    card("p1_r1", 260, 120, 230, 90, "Signup to Explore Rate",   tab=5),
    card("p1_r2", 500, 120, 230, 90, "Explore to Checkout Rate", tab=6),
    card("p1_r3", 740, 120, 230, 90, "Checkout to Payment Rate", tab=7),

    # Main funnel chart
    funnel_chart("p1_fn", 20, 220, 730, 370, "fact_funnel_events", "event_type", tab=8),

    # Donut — device type
    donut_chart("p1_dnt", 770, 220, 490, 220,
                "fact_funnel_events", "device_type", "Signup Users", tab=9),

    # Slicer — month
    slicer("p1_sl", 770, 450, 490, 80, "dim_date", "month_name", tab=10),

    # Bar — drop-off by region
    bar_chart("p1_bar", 770, 540, 490, 150,
              "fact_funnel_events", "region", ["Checkout Drop-off"], tab=11),
]

# ── PAGE 2: REVENUE & ORDERS ──────────────────────────────────────────────────
P2_ID = "b2c3d4e5f67890aa0002"

page2_visuals = [
    # Row 1 — Revenue KPI cards
    card("p2_c1",  20,  20, 225, 90, "Total Orders",    tab=0),
    card("p2_c2", 255,  20, 225, 90, "Gross Revenue",   tab=1),
    card("p2_c3", 490,  20, 225, 90, "Net Revenue",     tab=2),
    card("p2_c4", 725,  20, 225, 90, "Average Order Value", tab=3),
    card("p2_c5", 960,  20, 300, 90, "Gross Margin %",  tab=4),

    # Line chart — revenue trend
    line_chart("p2_ln", 20, 120, 820, 270,
               "dim_date", "year_month", ["Net Revenue", "Gross Revenue"], tab=5),

    # Donut — payment method
    donut_chart("p2_dnt", 860, 120, 400, 270,
                "fact_orders", "payment_method", "Net Revenue", tab=6),

    # Bar chart — revenue by category
    bar_chart("p2_bar", 20, 400, 820, 300,
              "fact_orders", "category", ["Net Revenue"], tab=7),

    # Cards — new vs returning
    card("p2_nc", 860, 400, 400, 130, "New Customer Revenue",       tab=8),
    card("p2_rc", 860, 540, 400, 130, "Returning Customer Revenue", tab=9),
    card("p2_nm", 860, 560, 200, 80, "New Customer %",              tab=10),
]

# ── PAGE 3: ENGAGEMENT TRENDS ─────────────────────────────────────────────────
P3_ID = "c3d4e5f6789abcde0003"

page3_visuals = [
    # Row 1 — Engagement KPIs
    card("p3_c1",  20,  20, 380, 90, "MAU",                 tab=0),
    card("p3_c2", 420,  20, 380, 90, "WAU",                 tab=1),
    card("p3_c3", 820,  20, 440, 90, "MoM Revenue Growth",  tab=2),

    # Line chart — users over time
    line_chart("p3_ln", 20, 120, 820, 270,
               "dim_date", "year_month", ["MAU"], tab=3),

    # Column chart — users by device
    col_chart("p3_cl", 860, 120, 400, 270,
              "fact_funnel_events", "device_type", ["Signup Users"], tab=4),

    # Row 3 — more KPIs
    card("p3_c4",  20, 400, 380, 90, "Total Sessions",        tab=5),
    card("p3_c5", 420, 400, 380, 90, "Revenue 7-Day Rolling Avg", tab=6),
    card("p3_c6", 820, 400, 440, 90, "WoW Checkout Rate Change",  tab=7),

    # Matrix — revenue by region x month
    matrix("p3_mx", 20, 500, 1240, 200,
           "dim_regions", "region",
           "dim_date", "month_short",
           ["Net Revenue"], tab=8),
]

# ── PAGE 4: KPI SCORECARD ─────────────────────────────────────────────────────
P4_ID = "d4e5f6789abcdef00004"

page4_visuals = [
    # Row 1 — Operational KPIs
    card("p4_c1",  20,  20, 290, 90, "Total Orders",      tab=0),
    card("p4_c2", 330,  20, 290, 90, "Net Revenue",       tab=1),
    card("p4_c3", 640,  20, 290, 90, "Average Order Value", tab=2),
    card("p4_c4", 950,  20, 310, 90, "Units Sold",        tab=3),

    # Row 2 — Quality KPIs
    card("p4_c5",  20, 120, 290, 90, "Gross Margin %",    tab=4),
    card("p4_c6", 330, 120, 290, 90, "Cancellation Rate", tab=5),
    card("p4_c7", 640, 120, 290, 90, "Return Rate",       tab=6),
    card("p4_c8", 950, 120, 310, 90, "New Customer %",    tab=7),

    # Row 3 — Funnel KPIs
    card("p4_c9",  20, 220, 290, 90, "Overall Conversion Rate",  tab=8),
    card("p4_ca", 330, 220, 290, 90, "Checkout to Payment Rate", tab=9),
    card("p4_cb", 640, 220, 290, 90, "Total Sessions",           tab=10),
    card("p4_cc", 950, 220, 310, 90, "Unique Buyers",            tab=11),

    # Matrix — full KPI breakdown by region
    matrix("p4_mx", 20, 330, 1240, 370,
           "dim_regions", "region",
           "dim_date", "month_short",
           ["Total Orders", "Net Revenue", "Average Order Value",
            "Overall Conversion Rate", "Cancellation Rate"], tab=12),
]

# ── WRITE FILES ───────────────────────────────────────────────────────────────

pages = [
    (P1_ID, "Funnel Analysis",    page1_visuals),
    (P2_ID, "Revenue & Orders",   page2_visuals),
    (P3_ID, "Engagement Trends",  page3_visuals),
    (P4_ID, "KPI Scorecard",      page4_visuals),
]

for pid, name, visuals in pages:
    page_folder = os.path.join(PAGES_DIR, pid)
    os.makedirs(page_folder, exist_ok=True)

    # Write page.json (metadata only — no visualContainers)
    page_path = os.path.join(page_folder, "page.json")
    with open(page_path, "w", encoding="utf-8") as f:
        json.dump(make_page(pid, name), f, indent=2)

    # Write each visual as its own file: visuals/{visualId}/visual.json
    for v in visuals:
        vis_folder = os.path.join(page_folder, "visuals", v["id"])
        os.makedirs(vis_folder, exist_ok=True)
        vis_path = os.path.join(vis_folder, "visual.json")
        with open(vis_path, "w", encoding="utf-8") as f:
            json.dump(make_visual(v), f, indent=2)

    print(f"  Written: {name} ({len(visuals)} visuals) -> {page_folder}")

# Update pages.json
pages_meta = {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [p[0] for p in pages],
    "activePageName": P1_ID
}
with open(os.path.join(REPORT_DIR, "pages", "pages.json"), "w", encoding="utf-8") as f:
    json.dump(pages_meta, f, indent=2)
print("  Updated pages.json")

print("\nAll 4 pages written successfully!")
print("Open Product-Funnel-Dashboard.pbip in Power BI Desktop.")
