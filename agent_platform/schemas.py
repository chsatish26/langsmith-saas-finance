from pydantic import BaseModel, Field
from typing import List, Optional

class Transaction(BaseModel):
    id: str
    date: str
    description: str
    merchant: Optional[str] = None
    amount: float
    type: str  # 'debit' or 'credit'
    account_id: str
    category: Optional[str] = None

class BorrowerProfile(BaseModel):
    borrower_id: str
    income_monthly: float
    debts_monthly: float
    fico: int
    home_price: float
    down_payment: float
    interest_rate: float = 0.065
    prop_tax_monthly: float = 300.0
    insurance_monthly: float = 120.0

class KPIRecord(BaseModel):  # retained for compatibility if needed
    ticker: str
    quarter: str
    revenue: float
    eps: float
    guidance_eps: float

# --- New schemas for Refinance use case ---
class LoanInfo(BaseModel):
    borrower_id: str
    loan_balance: float
    current_rate: float           # e.g., 0.065
    remaining_term_months: int    # e.g., 300

class RateInfo(BaseModel):
    date: str
    term_months: int
    rate: float                   # e.g., 0.058

class RefiAlert(BaseModel):
    borrower_id: str
    current_rate: float
    market_rate: float
    monthly_savings: float
    refi_alert: str               # 'Yes' or 'No'
    notes: List[str] = Field(default_factory=list)
