"""Generates SYNTHETIC opportunity data + weekly forecast snapshots for the Solar Deal Desk project.
All companies, people and outcomes are fictional. Seeded for reproducibility."""
import random, math, json, os
from datetime import date, timedelta
import pandas as pd

random.seed(42)
TODAY = date(2026, 10, 23)          # last weekly snapshot (Friday)
OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

STAGES = ["Prospecting", "Qualification", "Technical Review", "Proposal/Quote", "Negotiation"]
PROB = {"Prospecting": 10, "Qualification": 20, "Technical Review": 40, "Proposal/Quote": 60,
        "Negotiation": 80, "Closed Won": 100, "Closed Lost": 0}
FCAT = {"Prospecting": "Pipeline", "Qualification": "Pipeline", "Technical Review": "Pipeline",
        "Proposal/Quote": "Best Case", "Negotiation": "Commit", "Closed Won": "Closed", "Closed Lost": "Omitted"}

REGIONS = {  # weight, MWp range, base USD/Wp, win adj
    "India":        (0.40, (50, 300), 0.085, 0.00),
    "Middle East":  (0.18, (100, 500), 0.095, 0.03),
    "Australia":    (0.14, (40, 250), 0.110, 0.00),
    "Latin America": (0.16, (50, 300), 0.100, -0.03),
    "Europe":       (0.12, (20, 150), 0.115, -0.05),
}
SEGMENTS = {"IPP": (0.40, 0.05), "EPC": (0.30, 0.00), "Utility / PSU": (0.18, -0.05), "C&I open access": (0.12, 0.00)}
LEADS = {"Existing customer": (0.18, 0.20), "EPC referral": (0.20, 0.08), "Consultant / IE": (0.12, 0.05),
         "Tender portal": (0.22, -0.10), "Trade show": (0.14, -0.05), "Inbound web": (0.14, -0.12)}
VPROPS = {"Energy yield gain": (0.28, 0.08), "Bankability & warranty": (0.18, 0.10), "Lowest capex": (0.24, -0.10),
          "Fast delivery": (0.15, 0.00), "Local manufacturing": (0.15, 0.03)}
REPS = {"India": ["Ananya Rao", "Vikram Desai"], "Middle East": ["Omar Haddad"], "Australia": ["Sophie Turner"],
        "Latin America": ["Lucas Ferreira"], "Europe": ["Elena Novak"]}
COMPETITORS = ["Competitor A", "Competitor B", "Competitor C", "Fixed-tilt (no tracker)"]
LOSS = ["Price", "Lost to fixed-tilt", "Competitor features", "Delivery timeline", "Project delayed / cancelled", "Bankability concerns"]

P1 = ["Thar", "Deccan", "Gulf", "Outback", "Andes", "Iberia", "Sahel", "Kutch", "Coral", "Pampas", "Atlas", "Nilgiri",
      "Malwa", "Desert", "Southern", "Red Sea", "Sunbelt", "Helios", "Aravalli", "Bundel", "Karoo", "Mistral", "Banas", "Nimbus"]
P2 = ["Sun", "Solar", "Renewables", "Power", "Green", "Energy", "Light", "Volt", "Watt", "Ray"]
P3 = ["Pvt Ltd", "Ltd", "LLC", "Pty Ltd", "S.A.", "GmbH", "Holdings", "Developers"]


def pick(d):
    keys = list(d); w = [d[k][0] for k in keys]
    return random.choices(keys, weights=w)[0]


def acct(region):
    suf = {"India": ["Pvt Ltd", "Ltd"], "Middle East": ["LLC", "Holdings"], "Australia": ["Pty Ltd"],
           "Latin America": ["S.A."], "Europe": ["GmbH", "S.A.", "Ltd"]}[region]
    return f"{random.choice(P1)} {random.choice(P2)} {random.choice(suf)}"


def stage_on(row, d):
    """Stage of an opportunity on date d (None if not yet created)."""
    if d < row["created"]:
        return None
    if row["is_closed"] and d >= row["close"]:
        return row["final_stage"]
    span = max((row["close"] - row["created"]).days, 1)
    frac = (d - row["created"]).days / span
    idx = min(int(frac * 5), 4, row["max_idx"])
    return STAGES[idx]


rows = []
used = set()
for i in range(150):
    region = pick(REGIONS); seg = pick(SEGMENTS); lead = pick(LEADS); vp = pick(VPROPS)
    if vp == "Local manufacturing" and region != "India" and random.random() < 0.7:
        vp = "Energy yield gain"
    mw_lo, mw_hi = REGIONS[region][1]
    mw = int(round(random.uniform(mw_lo, mw_hi) / 5) * 5)
    disc = round(random.choice([0, 0.01, 0.02, 0.03, 0.03, 0.04, 0.05, 0.05, 0.06, 0.08, 0.10]), 2)
    price = round(REGIONS[region][2] * random.uniform(0.94, 1.06) * (1 - disc), 4)
    amount = round(mw * 1e6 * price, -3)
    cm = round(0.205 - 0.95 * disc + random.gauss(0, 0.015) - (0.015 if vp == "Lowest capex" else 0), 3)
    created = date(2025, 7, 1) + timedelta(days=random.randint(0, 470))
    cycle = int(min(max(random.lognormvariate(math.log(170), 0.35), 60), 420))
    close = created + timedelta(days=cycle)
    p = 0.33 + REGIONS[region][3] + SEGMENTS[seg][1] + LEADS[lead][1] + VPROPS[vp][1] + 0.6 * disc
    if vp == "Bankability & warranty" and seg == "Utility / PSU": p += 0.05
    if vp == "Lowest capex" and seg == "EPC": p -= 0.05
    p = min(max(p, 0.05), 0.85)
    is_closed = close <= TODAY
    won = random.random() < p
    if is_closed:
        final = "Closed Won" if won else "Closed Lost"
    else:
        final = None
    loss = comp = ""
    max_idx = 4
    if is_closed and not won:
        w = [3, 2, 2, 1, 1.2, 1]
        if vp == "Lowest capex": w[0] += 3
        if seg == "EPC": w[0] += 1.5
        if seg == "C&I open access" or region == "India": w[1] += 1.5
        if region in ("Europe", "Latin America"): w[5] += 1.5
        if vp == "Fast delivery": w[3] -= 0.5
        loss = random.choices(LOSS, weights=w)[0]
        comp = "Fixed-tilt (no tracker)" if loss == "Lost to fixed-tilt" else ("" if loss == "Project delayed / cancelled" else random.choice(COMPETITORS[:3]))
        max_idx = random.choices([1, 2, 3, 4], weights=[2, 3, 4, 3])[0]
    elif is_closed and won:
        comp = random.choice(COMPETITORS[:3] + [""])
    name = acct(region)
    while name in used: name = acct(region)
    used.add(name)
    rows.append(dict(created=created, close=close, is_closed=is_closed, final_stage=final, max_idx=max_idx,
                     account=name, region=region, segment=seg, lead=lead, vp=vp, mw=mw, price=price, disc=disc,
                     amount=amount, cm=cm, loss=loss, comp=comp, owner=random.choice(REPS[region]), win_p=round(p, 3)))

# Primary connected deal (values from Solar_Deal_Desk_Model.xlsx Deal_Summary)
# Values copied from 01-02_Quote_and_Energy_Model/Solar_Deal_Desk_Model.xlsx, Deal_Summary sheet
model = {"net_price_usd_wp": 0.08274881516587677, "discount": 0.03, "contract_usd": 8274881.5165876765, "cm_pct": 0.156067837597047}
rows.append(dict(created=date(2026, 8, 3), close=date(2026, 12, 15), is_closed=False, final_stage=None, max_idx=3,
                 account="Thar Sun Energy Pvt Ltd", region="India", segment="IPP", lead="EPC referral",
                 vp="Energy yield gain", mw=100, price=round(model["net_price_usd_wp"], 4), disc=model["discount"],
                 amount=round(model["contract_usd"], -3), cm=round(model["cm_pct"], 3), loss="", comp="Competitor B",
                 owner="Ananya Rao", win_p=None, primary=True))

recs = []
for k, r in enumerate(rows, start=1):
    st = stage_on(r, TODAY) if not r.get("primary") else "Proposal/Quote"
    r["stage_now"] = st
    recs.append({
        "Opportunity_ID": f"OPP-{k:04d}",
        "Opportunity_Name": f"{r['account'].split(' ')[0]} {r['mw']} MWp - {r['region']}",
        "Account_Name": r["account"],
        "Owner": r["owner"],
        "Region": r["region"],
        "Segment": r["segment"],
        "Lead_Source": r["lead"],
        "Value_Proposition": r["vp"],
        "Capacity_MWp": r["mw"],
        "Price_USD_per_Wp": r["price"],
        "Discount_Pct": r["disc"],
        "Amount_USD": r["amount"],
        "Est_Contribution_Margin_Pct": r["cm"],
        "Stage": st,
        "Probability_Pct": PROB[st],
        "Forecast_Category": FCAT[st],
        "Created_Date": r["created"].isoformat(),
        "Close_Date": r["close"].isoformat(),
        "Is_Closed": r["is_closed"],
        "Is_Won": st == "Closed Won",
        "Loss_Reason": r["loss"],
        "Competitor": r["comp"],
        "Sales_Cycle_Days": (r["close"] - r["created"]).days if r["is_closed"] else "",
        "Primary_Deal": bool(r.get("primary")),
        "Data_Label": "SYNTHETIC" if not r.get("primary") else "SYNTHETIC - primary connected deal",
    })
opp = pd.DataFrame(recs)
opp.to_csv(f"{OUT}/synthetic_opportunities.csv", index=False)

# Salesforce Data Import Wizard file (standard fields + custom fields)
sf = pd.DataFrame({
    "Opportunity Name": opp.Opportunity_Name, "Account Name": opp.Account_Name, "Stage": opp.Stage,
    "Close Date": opp.Close_Date, "Amount": opp.Amount_USD, "Probability (%)": opp.Probability_Pct,
    "Lead Source": opp.Lead_Source, "Type": "New Business", "Forecast Category": opp.Forecast_Category,
    "Region__c": opp.Region, "Segment__c": opp.Segment, "Value_Proposition__c": opp.Value_Proposition,
    "Capacity_MWp__c": opp.Capacity_MWp, "Price_USD_per_Wp__c": opp.Price_USD_per_Wp,
    "Discount__c": (opp.Discount_Pct * 100).round(1), "Contribution_Margin__c": (opp.Est_Contribution_Margin_Pct * 100).round(1),
    "Loss_Reason__c": opp.Loss_Reason, "Competitor__c": opp.Competitor, "External_ID__c": opp.Opportunity_ID,
    "Description": "SYNTHETIC portfolio data - not a real customer",
})
sf.to_csv(f"{OUT}/salesforce_import_opportunities.csv", index=False)
pd.DataFrame({"Account Name": sorted(opp.Account_Name.unique())}).assign(
    Type="Customer - Prospect", Description="SYNTHETIC portfolio data").to_csv(f"{OUT}/salesforce_import_accounts.csv", index=False)

# Weekly snapshots - stage of every opportunity each Friday
snaps = []
d = date(2026, 7, 3)
while d <= TODAY:
    for k, r in enumerate(rows, start=1):
        if r.get("primary"):
            st = None if d < r["created"] else ("Technical Review" if d < date(2026, 9, 18) else "Proposal/Quote")
        else:
            st = stage_on(r, d)
        if st is None: continue
        snaps.append({"Snapshot_Date": d.isoformat(), "Opportunity_ID": f"OPP-{k:04d}", "Stage": st,
                      "Probability_Pct": PROB[st], "Forecast_Category": FCAT[st], "Amount_USD": r["amount"],
                      "Close_Date": r["close"].isoformat(), "Region": r["region"]})
    d += timedelta(days=7)
pd.DataFrame(snaps).to_csv(f"{OUT}/weekly_pipeline_snapshots.csv", index=False)

print(opp.Stage.value_counts())
closed = opp[opp.Is_Closed & ~opp.Primary_Deal]
print("closed", len(closed), "win rate", round(closed.Is_Won.mean(), 3))
print(closed.groupby("Lead_Source").Is_Won.agg(["mean", "count"]))
print(closed.groupby("Value_Proposition").Is_Won.agg(["mean", "count"]))
print(closed[~closed.Is_Won].Loss_Reason.value_counts())
q4 = opp[(opp.Close_Date >= "2026-10-01") & (opp.Close_Date <= "2026-12-31")]
print("Q4 deals", len(q4), q4.groupby("Forecast_Category").Amount_USD.sum())
