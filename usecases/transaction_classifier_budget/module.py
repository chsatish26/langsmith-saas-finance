import os, json
from agent_platform.tools import load_transactions_csv, budget_insights, categorize
from agent_platform.schemas import Transaction
from agent_platform.orchestration import SimpleGraph
from agent_platform.utils import dump_json

def run(output_dir: str):
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'transactions_sample.csv')
    txs = load_transactions_csv(data_path)

    def classify_node(payload):
        txs = payload['transactions']
        out = []
        for t in txs:
            if not t.category:
                t.category = categorize(t)
            out.append(t)
        return {'transactions': out}

    def report_node(payload):
        insights = budget_insights(payload['transactions'])
        return {'insights': insights}

    g = (
        SimpleGraph()
        .add(lambda _: {'transactions': txs})
        .add(classify_node)
        .add(report_node)
    )

    result = g.run({'transactions': txs})
    os.makedirs(output_dir, exist_ok=True)
    dump_json(os.path.join(output_dir, 'a_insights.json'), result)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    run(output_dir=os.path.join('outputs','a'))
