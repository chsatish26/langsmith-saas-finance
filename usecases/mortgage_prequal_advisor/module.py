import os, json
from agent_platform.schemas import BorrowerProfile
from agent_platform.tools import compute_dti, compute_ltv, max_loan_estimate, policy_check
from agent_platform.orchestration import SimpleGraph
from agent_platform.utils import dump_json

def run(output_dir: str):
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'borrowers.jsonl')
    with open(data_path, 'r', encoding='utf-8') as f:
        profiles = [BorrowerProfile(**json.loads(l)) for l in f]

    def planner_node(payload):
        p = payload['profile']
        calc = {
            'dti': compute_dti(p),
            'ltv': compute_ltv(p),
            'max_loan': max_loan_estimate(p),
        }
        # keep both profile and calc in the payload
        return {'profile': p, 'calc': calc}

    def compliance_node(payload):
        p = payload['profile']
        # be robust: if calc got dropped upstream, recompute it
        calc = payload.get('calc')
        if calc is None:
            calc = {
                'dti': compute_dti(p),
                'ltv': compute_ltv(p),
                'max_loan': max_loan_estimate(p),
            }
        res = policy_check(p)
        return {
            'profile': p,
            'calc': calc,
            'policy_flags': res['flags'],
            'docs': res['docs'],
        }

    results = []
    for p in profiles:
        g = (
            SimpleGraph()
            .add(lambda _: {'profile': p})  # start
            .add(planner_node)              # adds 'calc'
            .add(compliance_node)           # consumes 'calc'
        )
        out = g.run({'profile': p})
        results.append({
            'borrower_id': p.borrower_id,
            'calc': out['calc'],
            'policy_flags': out['policy_flags'],
            'docs': out['docs'],
        })

    os.makedirs(output_dir, exist_ok=True)
    dump_json(os.path.join(output_dir, 'b_prequal.json'), {'results': results})
    print(json.dumps({'results': results}, indent=2))

if __name__ == '__main__':
    run(output_dir=os.path.join('outputs','b'))
