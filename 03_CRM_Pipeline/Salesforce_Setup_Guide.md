# Salesforce setup guide: Solar Deal Desk pipeline

**Time:** about 4–6 hours. **Cost:** free.
**Result:** a Salesforce Developer Edition org that holds the 151 synthetic opportunities, uses a solar-tracker sales process, and has a forecast dashboard you can screenshot for your portfolio.

> Every step below is done by hand in your own Developer Edition org. Take screenshots as you go (marked 📸).

---

## 0. Before you start (about 1 hour)

1. Sign up for a free **Developer Edition** org at developer.salesforce.com/signup. Use a username shaped like an email, e.g. `yourname@solardealdesk.dev`. It doesn't need to be a real inbox.
2. Complete these Trailhead modules and add the badges to LinkedIn:
   - *Salesforce Platform Basics*
   - *Data Management* (Data Import Wizard and Data Loader)
   - *Reports & Dashboards for Lightning Experience*
3. Files you'll use from this folder:

| File | Use |
|---|---|
| `salesforce_import_accounts.csv` | Step 3: import accounts |
| `salesforce_import_opportunities.csv` | Step 4: import opportunities |
| `weekly_pipeline_snapshots.csv` | Step 6: forecast history (optional) |

---

## 1. Configure the sales process (stages and probabilities)

Go to **Setup → Object Manager → Opportunity → Fields & Relationships → Stage**. Edit the picklist so it holds exactly these values:

| Stage | Probability | Forecast category | Meaning in a tracker sale |
|---|---|---|---|
| Prospecting | 10% | Pipeline | Project identified, contact made |
| Qualification | 20% | Pipeline | Size, timeline, budget and decision maker confirmed |
| Technical Review | 40% | Pipeline | Layout, energy yield and engineering review under way |
| Proposal/Quote | 60% | Best Case | Priced quote submitted, margin approved by the deal desk |
| Negotiation | 80% | Commit | Commercial terms, LDs and warranty under negotiation |
| Closed Won | 100% | Closed | Contract signed |
| Closed Lost | 0% | Omitted | Lost, with loss reason recorded |

Deactivate the default stages you don't use (e.g. *Needs Analysis*, *Id. Decision Makers*). Then add all stages to the sales process under **Setup → Sales Processes**. 📸

## 2. Create the custom fields

In **Object Manager → Opportunity → Fields & Relationships → New**, create the fields below. The API names must match the CSV headers exactly.

| Field label | API name | Type | Values |
|---|---|---|---|
| Region | `Region__c` | Picklist | India, Middle East, Australia, Latin America, Europe |
| Segment | `Segment__c` | Picklist | IPP, EPC, Utility / PSU, C&I open access |
| Value Proposition | `Value_Proposition__c` | Picklist | Energy yield gain, Bankability & warranty, Lowest capex, Fast delivery, Local manufacturing |
| Capacity (MWp) | `Capacity_MWp__c` | Number (8,1) | |
| Price (USD/Wp) | `Price_USD_per_Wp__c` | Number (4,4) | |
| Discount % | `Discount__c` | Percent (3,1) | |
| Contribution Margin % | `Contribution_Margin__c` | Percent (3,1) | |
| Loss Reason | `Loss_Reason__c` | Picklist | Price, Lost to fixed-tilt, Competitor features, Delivery timeline, Project delayed / cancelled, Bankability concerns |
| Competitor | `Competitor__c` | Picklist | Competitor A, Competitor B, Competitor C, Fixed-tilt (no tracker) |
| External ID | `External_ID__c` | Text (20), **External ID**, Unique | |

Also add these values to the standard **Lead Source** picklist: Existing customer, EPC referral, Consultant / IE, Tender portal, Trade show, Inbound web.

**Data-quality rule (optional but good to show).** Add a validation rule so a Closed Lost deal can't be saved without a loss reason:

```
AND( ISPICKVAL(StageName, "Closed Lost"), ISBLANK(TEXT(Loss_Reason__c)) )
```

Error message: *"Loss Reason is required for Closed Lost opportunities."* 📸
This ties directly to your Capgemini experience, where you enforced complete, audit-ready records before tickets could close.

## 3. Import the accounts

**Setup → Data Import Wizard → Accounts and Contacts → Add new records**. Upload `salesforce_import_accounts.csv` and map *Account Name*, *Type* and *Description*.

## 4. Import the opportunities

The Data Import Wizard does **not** support Opportunities, so use **Data Loader** (desktop) or **dataloader.io** (web, free tier).

1. Export your accounts (Id and Name) with Data Loader → *Export*, or with a report exported to CSV.
2. In Excel, add an `AccountId` column to `salesforce_import_opportunities.csv` using a lookup: `=INDEX(export!A:A, MATCH(B2, export!B:B, 0))`.
3. In Data Loader choose **Insert → Opportunity**. Map the columns (Opportunity Name → Name, Stage → StageName, Close Date → CloseDate, and so on), plus all the `__c` fields.
4. Check the record count: you should have **151 opportunities**. The *Thar Sun 100 MWp - India* opportunity should sit at **Proposal/Quote** with an amount of about **USD 8.27M**, matching the Excel deal model. 📸

## 5. Reports and dashboard

Create these reports (type: *Opportunities*) and add each to a dashboard named **"Solar Deal Desk - Global Pipeline"**:

| # | Report | Setup | Dashboard chart |
|---|---|---|---|
| 1 | Q4 forecast by category | Filter Close Date = Current FQ (or Oct–Dec 2026); group by Forecast Category; sum Amount | Stacked bar |
| 2 | Open pipeline by stage | Filter Closed = False; group by Stage | Funnel |
| 3 | Weighted pipeline by region | Group by Region; summary formula `AMOUNT:SUM * PROBABILITY:AVG` or row-level `Amount * Probability` | Bar |
| 4 | Win rate by lead source | Filter Closed = True; group by Lead Source; summary formula **`WON:SUM / CLOSED:SUM`** (Percent) | Horizontal bar |
| 5 | Win rate by value proposition | As #4, grouped by Value Proposition | Horizontal bar |
| 6 | Loss reasons | Stage = Closed Lost; group by Loss Reason | Donut |
| 7 | Deal-desk exceptions | Open deals where `Contribution_Margin__c` < 12% | Table |

📸 Screenshot the full dashboard. This is the main image for your portfolio and LinkedIn post.

**Cross-check:** reports #1, #4 and #6 should match the `Pipeline_Analytics.xlsx` sheets **Q4_Forecast** and **Win_Loss**. If they don't match, find out why before relying on either. Reconciling numbers is part of the job.

## 6. Weekly forecast history (optional)

Salesforce can't backfill history, so you have two choices:

- **Option A (real, going forward):** create a custom object *Pipeline Snapshot*, then use **Setup → Reporting Snapshots** to schedule a weekly copy of report #1 every Friday.
- **Option B (portfolio history):** import `weekly_pipeline_snapshots.csv` into that custom object with the Data Import Wizard, which does support custom objects. Then build a line chart of weighted forecast by Snapshot Date.

Either way, label the history clearly as synthetic.

## 7. Weekly routine to demonstrate

Every Friday the analyst should:

1. Refresh report #1 and record the forecast call: floor (closed + commit), most likely (weighted), stretch (closed + commit + best case).
2. Review deals whose close date has slipped, and deals with no activity in 14 days.
3. Run report #7 (deal-desk exceptions) and confirm margin approvals.
4. Send a one-paragraph forecast note to sales leadership.

A sample note, based on the Weekly_Forecast sheet:
*"Q4 weighted forecast is USD 352.8M (+23.4M WoW). Closed + Commit is USD 263.8M. The largest moves were deals advancing from Best Case to Commit. Thar Sun (100 MWp, India) is at Proposal/Quote with a USD 8.27M quote at 15.6% CM, within Sales Manager authority."*
