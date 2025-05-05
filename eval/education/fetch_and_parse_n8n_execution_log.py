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
        "workflow_name"      : str | None,
        "raw_log"            : full JSON,
        "final_out"          : str | None,
        "token_total"        : int,
        "input_query"        : str | None,
        "total_exec_ms"      : float,
        "tool_order"         : list[str],
        "tool_exec_ms"       : dict[node, ms],
        "tool_calls"         : dict[node, list[call_info]],
        "tool_call_counts"   : dict[node, int]
    }
    """
    # 0. Fetch
    resp = requests.get(webhook_url, params={"executionId": execution_id}, timeout=timeout)
    resp.raise_for_status()
    log = resp.json()
    run_data = log["data"]["resultData"]["runData"]

    # Workflow name (if present)
    workflow_name = _safe_get(log, ["workflowData", "name"]) or log.get("workflowId")

    # 1. Node order (with duplicates if a tool is called multiple times)
    node_times: List[Tuple[str, int]] = []
    for name, blocks in run_data.items():
        for block in blocks:
            start = _safe_get(block, ["startTime"])
            if isinstance(start, int):
                node_times.append((name, start))

    node_times.sort(key=lambda x: x[1])  # Sort by actual call time
    tool_order = [n for n, _ in node_times]

    # 2. Final output
    final_out = None
    for name, _ in reversed(node_times):
        maybe = _safe_get(run_data, [name, 0, "data", "main", 0, 0, "json"])
        if isinstance(maybe, dict) and "output" in maybe:
            final_out = maybe["output"]
            break

    # 3. Gather per-tool call records
    tool_calls: Dict[str, List[Dict[str, Any]]] = {}
    tool_exec_ms: Dict[str, float] = {}
    for name, blocks in run_data.items():
        calls = []
        total_exec = 0
        for block in blocks:
            start_time = _safe_get(block, ["startTime"])
            exec_time  = _safe_get(block, ["executionTime"])
            if isinstance(exec_time, (int, float)):
                total_exec = exec_time            # keep last exec-time

            # -------- INPUT ------------
            raw_in_block = block.get("inputOverride") or block.get("data", {})

            inp = None
            # Check for specific AI node input structures first
            if "ai_tool" in raw_in_block:
                # Specifically get the 'query' part for tools
                inp = _safe_get(raw_in_block, ["ai_tool", 0, 0, "json", "query"])
            elif "ai_languageModel" in raw_in_block:
                # Specifically get the 'messages' for language models
                inp = _safe_get(raw_in_block, ["ai_languageModel", 0, 0, "json", "messages"])
            elif "ai_vectorStore" in raw_in_block:
                 # Assuming vector stores might use 'query' or maybe 'text'?
                 # Prioritize 'query', fallback to the whole json if 'query' not found
                inp = _safe_get(raw_in_block, ["ai_vectorStore", 0, 0, "json", "query"])
                if inp is None: # Fallback if no 'query' key
                     inp = _safe_get(raw_in_block, ["ai_vectorStore", 0, 0, "json"])
            # Fallback for generic nodes (like Webhook trigger)
            elif "main" in raw_in_block:
                maybe = _safe_get(raw_in_block, ["main", 0, 0, "json"])
                if isinstance(maybe, dict):
                    # Prefer 'body' if it exists (common for webhooks), else take the whole json
                    inp = maybe.get("body", maybe)
            # Broadest fallback: use the raw block if it's not empty and none of the above matched
            elif raw_in_block and raw_in_block != {}: # Ensure it's not just the default empty dict
                inp = raw_in_block


            # -------- OUTPUT -----------
            data_block = block.get("data", {})
            out = None
            if "ai_tool" in data_block:
                # Response is usually directly under json
                out = _safe_get(data_block, ["ai_tool", 0, 0, "json", "response"])
            elif "ai_vectorStore" in data_block:
                 # Check if response structure is consistent
                out = _safe_get(data_block, ["ai_vectorStore", 0, 0, "json", "response"])
            elif "ai_languageModel" in data_block:
                 # Get the generated text or the whole response block
                 # Prioritize the text itself if possible
                maybe_text = _safe_get(data_block, ["ai_languageModel", 0, 0, "json", "response", "generations", 0, 0, "text"])
                if maybe_text is not None:
                    out = maybe_text
                else: # Fallback to the whole response object
                    out = _safe_get(data_block, ["ai_languageModel", 0, 0, "json", "response"])
            elif "main" in data_block:
                # For generic nodes, output might just be the json itself
                maybe = _safe_get(data_block, ["main", 0, 0, "json"])
                if isinstance(maybe, dict):
                    out = maybe

            # Only append if we found meaningful input OR output
            if inp is not None or out is not None:
                calls.append({
                    "startTime": start_time,
                    "executionTime": exec_time,
                    "input": inp,
                    "output": out,
                })

        if calls:
            tool_calls[name] = calls
            tool_exec_ms[name] = total_exec

    # 4. Total OpenAI tokens  ── sum every call in every "OpenAI Chat Model" node
    token_total = 0
    for node_name, blocks in run_data.items():
        if not node_name.startswith("OpenAI Chat Model"):
            continue

        for blk in blocks:                              
            total = _safe_get(
                blk,                                        # look inside this block
                ["data", "ai_languageModel", 0, 0, "json", "tokenUsage", "totalTokens"]
            )
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

    # 7. Compute call counts
    tool_call_counts = {name: len(calls) for name, calls in tool_calls.items()}

    # 8. Assemble result
    return {
        "workflow_name": workflow_name,
        "raw_log": log,
        "final_out": final_out,
        "token_total": token_total,
        "input_query": input_query,
        "total_exec_ms": total_exec_ms,
        "tool_order": tool_order,
        "tool_exec_ms": tool_exec_ms,
        "tool_calls": tool_calls,
        "tool_call_counts": tool_call_counts,
    }
