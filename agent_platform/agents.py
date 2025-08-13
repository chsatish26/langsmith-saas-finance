from typing import Any, Dict, List
from .memory import ConversationMemory
from .schemas import RefiAlert, LoanInfo, RateInfo
from . import tools
from .utils import now_ms

class AgentBase:
    def __init__(self, id: str, tools_allowed: List[str], memory_turns: int = 6):
        self.id = id
        self.tools_allowed = set(tools_allowed)
        self.memory = ConversationMemory(max_turns=memory_turns)

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

# --- Use Case A agents (kept simple; reuse tools via modules) ---
# (A's specific agents live in respective modules for brevity)

# --- Use Case B agents (Planner & Compliance live in modules) ---

# --- Use Case C agents (Refi) ---
class RateRetrieverAgent(AgentBase):
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        rates: List[RateInfo] = payload['rates']
        # pick best available rate for matching term (or lowest overall as fallback)
        if 'term_months' in payload and payload['term_months']:
            tm = payload['term_months']
            term_rates = [r.rate for r in rates if r.term_months == tm]
            market_rate = min(term_rates) if term_rates else min(r.rate for r in rates)
        else:
            market_rate = min(r.rate for r in rates)
        self.memory.add('system', f'Selected market rate {market_rate:.4f}')
        return {'market_rate': market_rate}

class SavingsCalculatorAgent(AgentBase):
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        loans: List[LoanInfo] = payload['loans']
        market_rate: float = payload['market_rate']
        out = []
        for loan in loans:
            savings = tools.calculate_savings(loan, market_rate)
            out.append({'borrower_id': loan.borrower_id, 'current_rate': loan.current_rate, 'market_rate': market_rate, 'monthly_savings': savings})
        self.memory.add('system', f'Computed savings for {len(out)} loans')
        return {'savings': out}

class AlertAgent(AgentBase):
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        threshold = payload.get('threshold', 150.0)
        results = []
        for row in payload['savings']:
            alert = tools.should_alert(row['monthly_savings'], threshold)
            results.append(RefiAlert(
                borrower_id=row['borrower_id'],
                current_rate=row['current_rate'],
                market_rate=row['market_rate'],
                monthly_savings=row['monthly_savings'],
                refi_alert='Yes' if alert else 'No',
                notes=[] if alert else ['Below savings threshold']
            ))
        self.memory.add('system', f'Alert flagged for {sum(1 for r in results if r.refi_alert=="Yes")} borrowers')
        return {'alerts': results}
