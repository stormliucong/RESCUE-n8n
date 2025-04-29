import requests
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Utility helpers
def _safe_get(d: dict, path: List[str]):
    """
    Walk a list of keys/indices and return value or None.
    """
    cur = d
    for p in path:
        try:
            cur = cur[p]
        except (KeyError, IndexError, TypeError):
            return None
    return cur


# Main parser
def fetch_and_parse_n8n_execution_log(execution_id: int, webhook_url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Download a detailed n8n execution log, parse key metrics, and return them.

    Parameters
    ----------
    execution_id : int
        ID of the execution to fetch.
    webhook_url : str
        The webhook endpoint that returns detailed execution logs when
        called with ?executionId=<id>.
    timeout : int
        HTTP timeout (seconds).

    Returns
    -------
    dict : {
        "workflow_name" : str | None,
        "raw_log"       : full JSON,
        "final_out"     : str | None,
        "tools_used"    : list[str],
        "token_total"   : int,
        "tool_outputs"  : dict[node, payload],
        "input_query"   : str | None,
        "total_exec_ms" : float,
        "tool_exec_ms"  : dict[node, ms],
        "tool_order"    : list[str]
    }
    """
    # 0. Fetch
    resp = requests.get(webhook_url, params={"executionId": execution_id}, timeout=timeout)
    resp.raise_for_status()
    log = resp.json()
    run_data = log["data"]["resultData"]["runData"]

    # Workflow name (if present)
    workflow_name = _safe_get(log, ["workflowData", "name"]) or log.get("workflowId")

    # 1. Node order
    node_times: List[Tuple[str, int]] = []
    for name, blocks in run_data.items():
        start = _safe_get(blocks, [0, "startTime"])
        if isinstance(start, int):
            node_times.append((name, start))
    node_times.sort(key=lambda x: x[1])
    tool_order = [n for n, _ in node_times]

    # 2. Final output
    final_out = None
    for name, _ in reversed(node_times):
        maybe = _safe_get(run_data, [name, 0, "data", "main", 0, 0, "json"])
        if isinstance(maybe, dict) and "output" in maybe:
            final_out = maybe["output"]
            break

    # 3. Tools, outputs, exec times
    tools_used, tool_outputs, tool_exec_ms = [], {}, {}
    for name, blocks in run_data.items():
        data_block = _safe_get(blocks, [0, "data"])
        if data_block is None:
            continue

        # exec time
        exec_ms = _safe_get(blocks, [0, "executionTime"])
        if isinstance(exec_ms, (int, float)):
            tool_exec_ms[name] = exec_ms

        # payload sniffing
        payload = None
        if "ai_tool" in data_block:
            payload = _safe_get(data_block, ["ai_tool", 0, 0, "json", "response"])
        elif "ai_vectorStore" in data_block:
            payload = _safe_get(data_block, ["ai_vectorStore", 0, 0, "json", "response"])
        elif "ai_languageModel" in data_block:
            payload = _safe_get(data_block, ["ai_languageModel", 0, 0, "json", "response"])
        elif "main" in data_block:
            maybe_json = _safe_get(data_block, ["main", 0, 0, "json"])
            if isinstance(maybe_json, dict):
                payload = maybe_json

        if payload is not None:
            tools_used.append(name)
            tool_outputs[name] = payload

    # 4. Total OpenAI tokens
    token_total = 0
    for name in run_data:
        if name.startswith("OpenAI Chat Model"):
            total = _safe_get(run_data, [name, 0, "data", "ai_languageModel", 0, 0,
                                         "json", "tokenUsage", "totalTokens"])
            if isinstance(total, int):
                token_total += total

    # 5. Input query
    input_query = None
    for node in tool_order:
        jq = _safe_get(run_data, [node, 0, "data", "main", 0, 0, "json"])
        if isinstance(jq, dict):
            for key in ("chatInput", "query"):
                if key in jq and isinstance(jq[key], str):
                    input_query = jq[key]
                    break
            if input_query:
                break
            body_prompt = _safe_get(jq, ["body", "prompt"])
            if isinstance(body_prompt, str):
                input_query = body_prompt
                break

    # 6. Wall-clock duration
    t0 = datetime.fromisoformat(log["startedAt"].replace("Z", "+00:00"))
    t1 = datetime.fromisoformat(log["stoppedAt"].replace("Z", "+00:00"))
    total_exec_ms = (t1 - t0).total_seconds() * 1000

    # 7. Assemble
    return {
        "workflow_name": workflow_name,
        "raw_log": log,
        "final_out": final_out,
        "tools_used": tools_used,
        "token_total": token_total,
        "tool_outputs": tool_outputs,
        "input_query": input_query,
        "total_exec_ms": total_exec_ms,
        "tool_exec_ms": tool_exec_ms,
        "tool_order": tool_order,
    }