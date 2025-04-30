from fetch_and_parse_n8n_execution_log import fetch_and_parse_n8n_execution_log


result = fetch_and_parse_n8n_execution_log(
    execution_id=2198,
    webhook_url="https://congliu.app.n8n.cloud/webhook/9e17d9af-78a5-46df-bb0f-76376c1eba3e"
)

# print(result["final_out"])
print(result["workflow_name"])
print("Tools used:", result["tools_used"])
print("Token total:", result["token_total"])


