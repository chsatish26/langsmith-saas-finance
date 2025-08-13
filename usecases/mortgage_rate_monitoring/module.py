import os, json
from agent_platform.schemas import LoanInfo, RateInfo
from agent_platform.tools import load_loans_jsonl, load_rates_jsonl
from agent_platform.agents import RateRetrieverAgent, SavingsCalculatorAgent, AlertAgent
from agent_platform.orchestration import SimpleGraph
from agent_platform.utils import dump_json

def run(output_dir: str, threshold: float = 150.0):
    base = os.path.dirname(__file__)
    loans_path = os.path.join(base, 'data', 'loans.jsonl')
    rates_path = os.path.join(base, 'data', 'rates.jsonl')

    loans = load_loans_jsonl(loans_path)
    rates = load_rates_jsonl(rates_path)

    rate_agent = RateRetrieverAgent('rate_retriever', tools_allowed=['load_rates'])
    savings_agent = SavingsCalculatorAgent('savings', tools_allowed=['calculate_savings'])
    alert_agent = AlertAgent('alert', tools_allowed=['should_alert'])

    g = (
        SimpleGraph()
        .add(lambda _: {'rates': rates, 'term_months': None})
        .add(rate_agent.run)
        .add(lambda x: {'loans': loans, 'market_rate': x['market_rate']})
        .add(savings_agent.run)
        .add(lambda x: {'savings': x['savings'], 'threshold': threshold})
        .add(alert_agent.run)   
    )
    out = g.run({})
    os.makedirs(output_dir, exist_ok=True)
    dump_json(os.path.join(output_dir, 'c_refi_alerts.json'), {
        'market_rate': out['alerts'][0].market_rate if out['alerts'] else None,
        'alerts': [a.model_dump() for a in out['alerts']]
    })
    print(json.dumps({'alerts': [a.model_dump() for a in out['alerts']]}, indent=2))

if __name__ == '__main__':
    run(output_dir=os.path.join('outputs','c'))
