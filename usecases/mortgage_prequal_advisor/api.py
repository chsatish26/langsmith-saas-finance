# Minimal LangGraph graph that wraps your existing functions
from typing import Dict, Any
from langgraph.graph import StateGraph
from agent_platform.tools import load_transactions_csv, budget_insights, categorize

def _classify_node(state: Dict[str, Any]) -> Dict[str, Any]:
    txs = state["transactions"]
    for t in txs:
        if not t.category:
            t.category = categorize(t)
    return {"transactions": txs}

def _report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return {"insights": budget_insights(state["transactions"])}

def build_graph():
    sg = StateGraph(dict)
    sg.add_node("classify", _classify_node)
    sg.add_node("report", _report_node)
    sg.set_entry_point("classify")
    sg.add_edge("classify", "report")
    sg.set_finish_point("report")
    return sg.compile()
