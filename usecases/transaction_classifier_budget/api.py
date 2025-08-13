from typing import Dict, Any, List
from langgraph.graph import StateGraph
from agent_platform.tools import load_loans_jsonl, load_rates_jsonl, calculate_savings, should_alert

def _rate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    rates = state["rates"]
    term = state.get("term_months")
    if term:
        candidates = [r["rate"] if isinstance(r, dict) else r.rate for r in rates if (r["term_months"] if isinstance(r, dict) else r.term_months) == term]
        market_rate = min(candidates) if candidates else min(r["rate"] if isinstance(r, dict) else r.rate for r in rates)
    else:
        market_rate = min(r["rate"] if isinstance(r, dict) else r.rate for r in rates)
    return {"market_rate": market_rate}

def _savings_node(state: Dict[str, Any]) -> Dict[str, Any]:
    loans = state["loans"]
    mr = state["market_rate"]
    out = []
    for loan in loans:
        # allow dict or pydantic model
        lb = loan["loan_balance"] if isinstance(loan, dict) else loan.loan_balance
        cr = loan["current_rate"] if isinstance(loan, dict) else loan.current_rate
        tm = loan["remaining_term_months"] if isinstance(loan, dict) else loan.remaining_term_months
        # quick inline monthly payment delta (reuse of calculate_savings is fine if you convert)
        from agent_platform.schemas import LoanInfo
        li = LoanInfo(borrower_id=(loan["borrower_id"] if isinstance(loan, dict) else loan.borrower_id),
                      loan_balance=lb, current_rate=cr, remaining_term_months=tm)
        out.append({"borrower_id": li.borrower_id, "current_rate": cr, "market_rate": mr, "monthly_savings": calculate_savings(li, mr)})
    return {"savings": out}

def _alert_node(state: Dict[str, Any]) -> Dict[str, Any]:
    threshold = state.get("threshold", 150.0)
    alerts = []
    for row in state["savings"]:
        alerts.append({
            "borrower_id": row["borrower_id"],
            "current_rate": row["current_rate"],
            "market_rate": row["market_rate"],
            "monthly_savings": row["monthly_savings"],
            "refi_alert": "Yes" if should_alert(row["monthly_savings"], threshold) else "No"
        })
    return {"alerts": alerts}

def build_graph():
    sg = StateGraph(dict)
    sg.add_node("rate", _rate_node)
    sg.add_node("savings", _savings_node)
    sg.add_node("alert", _alert_node)
    sg.set_entry_point("rate")
    sg.add_edge("rate", "savings")
    sg.add_edge("savings", "alert")
    sg.set_finish_point("alert")
    return sg.compile()
