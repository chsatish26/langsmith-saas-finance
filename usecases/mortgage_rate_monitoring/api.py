from typing import Dict, Any
from langgraph.graph import StateGraph
from agent_platform.tools import compute_dti, compute_ltv, max_loan_estimate, policy_check

def _planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    p = state["profile"]
    return {"profile": p, "calc": {
        "dti": compute_dti(p),
        "ltv": compute_ltv(p),
        "max_loan": max_loan_estimate(p),
    }}

def _compliance_node(state: Dict[str, Any]) -> Dict[str, Any]:
    p = state["profile"]
    res = policy_check(p)
    return {"profile": p, "calc": state["calc"], "policy_flags": res["flags"], "docs": res["docs"]}

def build_graph():
    sg = StateGraph(dict)
    sg.add_node("planner", _planner_node)
    sg.add_node("compliance", _compliance_node)
    sg.set_entry_point("planner")
    sg.add_edge("planner", "compliance")
    sg.set_finish_point("compliance")
    return sg.compile()
