from typing import List, Dict, Any
import duckdb, re
from .schemas import Transaction, BorrowerProfile, LoanInfo, RateInfo

# ---- Use Case A tools ----

def load_transactions_csv(path: str) -> List[Transaction]:
    import csv
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(Transaction(**{
                'id': r['id'],
                'date': r['date'],
                'description': r['description'],
                'merchant': r.get('merchant') or None,
                'amount': float(r['amount']),
                'type': r['type'],
                'account_id': r['account_id'],
                'category': r.get('category') or None
            }))
    return rows

MERCHANT_MAP = {
    'WHOLEFOODS': 'Groceries',
    'WALMART': 'Groceries',
    'SHELL': 'Gas',
    'UBER': 'Transport',
    'NETFLIX': 'Entertainment',
    'RENT *': 'Rent',
}

def categorize(tx: Transaction) -> str:
    desc = (tx.merchant or tx.description or '').upper()
    for pat, cat in MERCHANT_MAP.items():
        if pat.endswith('*'):
            if desc.startswith(pat[:-1]):
                return cat
        if pat in desc:
            return cat
    if re.search(r'GROC(ERY|ERIES)?|MARKET', desc):
        return 'Groceries'
    if re.search(r'FUEL|GAS|SHELL|EXXON', desc):
        return 'Gas'
    if re.search(r'UBER|LYFT|TAXI', desc):
        return 'Transport'
    if re.search(r'RENT', desc):
        return 'Rent'
    if re.search(r'NETFLIX|SPOTIFY|HULU', desc):
        return 'Entertainment'
    return 'Other'

def budget_insights(transactions: List[Transaction]) -> Dict[str, Any]:
    import pandas as pd, duckdb
    df = pd.DataFrame([t.model_dump() for t in transactions])
    if 'category' not in df.columns:
        df['category'] = None
    df['category'] = df['category'].fillna('Unknown')
    # debit == spend (credits treated as 0)
    df['spend'] = df.apply(lambda r: r['amount'] if r['type'] == 'debit' else 0.0, axis=1)

    con = duckdb.connect()
    cat = con.execute("""
        SELECT category, ROUND(SUM(spend), 2) AS total_spend, COUNT(*) AS n
        FROM df
        GROUP BY category
        ORDER BY total_spend DESC
    """).fetchdf().to_dict(orient='records')

    top_merchants = con.execute("""
        SELECT
          COALESCE(merchant, description) AS merchant,
          ROUND(SUM(spend), 2) AS total_spend
        FROM df
        GROUP BY COALESCE(merchant, description)
        ORDER BY total_spend DESC
        LIMIT 5
    """).fetchdf().to_dict(orient='records')

    recurring = con.execute("""
        SELECT
          COALESCE(merchant, description) AS merchant,
          COUNT(*) AS hits
        FROM df
        GROUP BY COALESCE(merchant, description)
        HAVING COUNT(*) >= 2
        ORDER BY hits DESC
    """).fetchdf().to_dict(orient='records')

    return {
        'by_category': cat,
        'top_merchants': top_merchants,
        'possible_recurring': recurring
    }


# ---- Use Case B tools ----

def compute_dti(profile: BorrowerProfile) -> float:
    piti = compute_piti(profile)
    monthly = profile.debts_monthly + piti
    return round(monthly / max(profile.income_monthly, 1), 4)

def compute_ltv(profile: BorrowerProfile) -> float:
    loan = profile.home_price - profile.down_payment
    return round(loan / max(profile.home_price, 1), 4)

def compute_piti(profile: BorrowerProfile) -> float:
    loan = profile.home_price - profile.down_payment
    r = profile.interest_rate/12
    n = 360
    m = loan * (r*(1+r)**n)/(((1+r)**n)-1)
    return round(m + profile.prop_tax_monthly + profile.insurance_monthly, 2)

def policy_check(profile: BorrowerProfile) -> Dict[str, Any]:
    flags = []
    if compute_dti(profile) > 0.43:
        flags.append('DTI>43%')
    if profile.fico < 620:
        flags.append('LowFICO')
    if compute_ltv(profile) > 0.97:
        flags.append('HighLTV')
    return {'flags': flags, 'docs': ['Pay stubs', 'W-2', 'Bank statements']}

def max_loan_estimate(profile: BorrowerProfile) -> float:
    target_dti = 0.36
    allowable = max(profile.income_monthly * target_dti - profile.debts_monthly, 0)
    r = profile.interest_rate/12
    n = 360
    if r == 0: return 0.0
    principal = allowable * (((1+r)**n - 1)/(r*(1+r)**n))
    return round(principal, 2)

# ---- Use Case C tools (Refi) ----

def load_loans_jsonl(path: str) -> List[LoanInfo]:
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            rows.append(LoanInfo(**__import__('json').loads(line)))
    return rows

def load_rates_jsonl(path: str) -> List[RateInfo]:
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            rows.append(RateInfo(**__import__('json').loads(line)))
    return rows

def monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    if annual_rate == 0:
        return principal / max(term_months,1)
    r = annual_rate/12
    n = term_months
    m = principal * (r*(1+r)**n)/(((1+r)**n)-1)
    return m

def calculate_savings(loan: LoanInfo, market_rate: float) -> float:
    current_pmt = monthly_payment(loan.loan_balance, loan.current_rate, loan.remaining_term_months)
    new_pmt = monthly_payment(loan.loan_balance, market_rate, loan.remaining_term_months)
    return round(current_pmt - new_pmt, 2)

def should_alert(monthly_savings: float, threshold: float = 150.0) -> bool:
    return monthly_savings >= threshold
