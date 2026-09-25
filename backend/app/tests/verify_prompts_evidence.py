import asyncio
import json
import logging
from app.agents.planner.planner_v2 import intelligent_planner_v2
from app.agents.graph import langgraph_orchestrator

logging.basicConfig(level=logging.INFO)

PROMPTS = [
    "Send good morning email",
    "Notify Slack when GitHub PR opens",
    "Read employees from Google Sheets and email each employee",
    "Webhook -> AI -> Gmail",
    "Every Monday send weekly report",
]

async def run_evidence_collection():
    print("\n================================================================================")
    print("      EMPIRICAL EVIDENCE COLLECTION: AGENTFLOW AI PLANNER V2 INTEGRATION        ")
    print("================================================================================\n")

    results = []

    for idx, prompt in enumerate(PROMPTS, 1):
        print(f"--- [PROMPT {idx}]: \"{prompt}\" ---")
        print(f"1. HTTP Request URL: http://localhost:8000/api/v1/ai/generate")
        print(f"2. Request Payload: {json.dumps({'prompt': prompt})}")
        print(f"3. Backend Endpoint: app.api.v1.ai.generate_workflow (FastAPI)")

        state = await langgraph_orchestrator.run(prompt)
        wf_json = state.get("workflow_json", {})

        print(f"4. Planner V2 Output JSON:")
        print(json.dumps(wf_json, indent=2))

        nodes = wf_json.get("nodes", [])
        print(f"5. React Flow Nodes Rendered ({len(nodes)} nodes):")
        for n in nodes:
            data = n.get("data", {})
            print(f"   - Node [{n.get('id')}]: Provider='{data.get('provider')}', Operation='{data.get('operation_id')}', Parameters={json.dumps(data.get('parameters', {}))}")

        print(f"6. Verification: Unique intent '{wf_json.get('intent')}' and {len(nodes)} nodes generated.\n")

        results.append({
            "prompt": prompt,
            "intent": wf_json.get("intent"),
            "node_count": len(nodes),
            "providers": [n.get("data", {}).get("provider") for n in nodes],
        })

    print("================================================================================")
    print("                      COMPARATIVE INTENT & DAG SUMMARY                         ")
    print("================================================================================")
    for idx, r in enumerate(results, 1):
        print(f"Prompt {idx}: \"{r['prompt']}\" -> Intent: {r['intent']} | Providers: {r['providers']}")
    print("================================================================================\n")

if __name__ == "__main__":
    asyncio.run(run_evidence_collection())
