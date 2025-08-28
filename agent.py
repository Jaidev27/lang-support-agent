
import json
from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END

class CommonMcpClient:
    """Simulates a client for abilities with no external data dependencies."""
    def parse_request_text(self, query: str) -> Dict[str, Any]:
        print("  📞 Calling COMMON Server: parse_request_text")
        # Simulate NLP: identify intent
        if "error code" in query.lower():
            return {"intent": "technical_support", "structured_query": query}
        return {"intent": "general_inquiry", "structured_query": query}

    def normalize_fields(self, ticket_id: str) -> Dict[str, str]:
        print("  📞 Calling COMMON Server: normalize_fields")
        # Simulate data cleaning
        return {"normalized_ticket_id": ticket_id.strip().upper()}

    def add_flags_calculations(self, priority: int, query: str) -> Dict[str, Any]:
        print("  📞 Calling COMMON Server: add_flags_calculations")
        # Simulate risk calculation
        is_urgent = "urgent" in query.lower() or priority > 3
        return {"is_urgent_flag": is_urgent, "calculated_priority": priority * 1.5 if is_urgent else priority}

    def solution_evaluation(self, kb_article: Dict[str, Any]) -> Dict[str, int]:
        print("  📞 Calling COMMON Server: solution_evaluation")
        # Simulate scoring a solution based on relevance.
        # Let's pretend articles about "error code" are highly relevant.
        score = 95 if "error code" in kb_article.get("title", "").lower() else 75
        return {"solution_score": score}

    def response_generation(self, customer_name: str, query: str, kb_article: Dict[str, Any]) -> Dict[str, str]:
        print("  📞 Calling COMMON Server: response_generation")
        # Simulate drafting a response
        response = (
            f"Hello {customer_name},\n\n"
            f"Thank you for contacting us about your query: '{query[:30]}...'.\n\n"
            f"Based on our knowledge base, here is a relevant article that might help: '{kb_article['title']}'.\n\n"
            f"Summary: {kb_article['summary']}\n\n"
            f"Regards,\nLangie Support Agent"
        )
        return {"generated_response": response}

class AtlasMcpClient:
    """Simulates a client for abilities requiring external system interaction."""
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        print("  📞 Calling ATLAS Server: extract_entities")
        # Simulate entity extraction (e.g., product names, codes)
        entities = []
        if "Pro-Widget X" in query:
            entities.append("Pro-Widget X")
        if "error code 42" in query:
            entities.append("error code 42")
        return {"extracted_entities": entities}

    def enrich_records(self, email: str) -> Dict[str, Any]:
        print("  📞 Calling ATLAS Server: enrich_records")
        # Simulate fetching customer data from a CRM
        return {
            "customer_sla": "Gold",
            "historical_ticket_count": 5
        }

    def knowledge_base_search(self, entities: List[str]) -> Dict[str, Dict]:
        print("  📞 Calling ATLAS Server: knowledge_base_search")
        # Simulate searching a KB
        if "error code 42" in entities:
            return {
                "retrieved_kb_article": {
                    "id": "KB-123",
                    "title": "Resolving Error Code 42 on Pro-Widget X",
                    "summary": "This error is typically caused by a firmware mismatch. To resolve, please follow the steps to update the firmware..."
                }
            }
        return {"retrieved_kb_article": {}}

    def escalation_decision(self, ticket_id: str) -> Dict[str, str]:
        print("  📞 Calling ATLAS Server: escalation_decision")
        # Simulate assigning to a human agent in a ticketing system
        return {"escalation_status": "Assigned to Tier 2 Support"}

    def update_ticket(self, ticket_id: str, status: str, assignee: str) -> Dict[str, str]:
        print(f"  📞 Calling ATLAS Server: update_ticket (Status: {status})")
        return {"ticket_update_status": "SUCCESS"}

    def close_ticket(self, ticket_id: str) -> Dict[str, str]:
        print(f"  📞 Calling ATLAS Server: close_ticket")
        return {"ticket_close_status": "SUCCESS"}

    def trigger_notifications(self, email: str, message: str) -> Dict[str, str]:
        print(f"  📞 Calling ATLAS Server: trigger_notifications")
        # Simulate sending an email
        return {"notification_status": "SENT"}
    
    # We will combine execute_api_calls with trigger_notifications for simplicity in this demo
    def execute_api_calls(self, email: str, message: str) -> Dict[str, str]:
        return self.trigger_notifications(email, message)


# ==============================================================================
# 2. STATE MANAGEMENT
# ==============================================================================
# This defines the "memory" of our agent. It's passed between stages.

class AgentState(TypedDict):
    # --- Input Fields ---
    customer_name: str
    email: str
    query: str
    priority: int
    ticket_id: str
    
    # --- State Fields (added during workflow) ---
    log: List[str]  # To track the agent's journey
    structured_data: Dict[str, Any]
    enriched_data: Dict[str, Any]
    retrieved_kb_article: Dict[str, Any]
    decision: Dict[str, Any]
    final_response: str
    final_status: Literal["RESOLVED", "ESCALATED"]


# ==============================================================================
# 3. STAGE (NODE) IMPLEMENTATIONS
# ==============================================================================
# Each function represents a node in our graph.

def stage_intake(state: AgentState) -> AgentState:
    """📥 Stage 1: INTAKE - Accept the initial payload."""
    log_message = "✅ STAGE: INTAKE - Payload accepted."
    print(log_message)
    state['log'].append(log_message)
    # No abilities to call, just accepting the initial state
    return state

def stage_understand(state: AgentState) -> AgentState:
    """🧠 Stage 2: UNDERSTAND - Parse text and extract entities."""
    log_message = "✅ STAGE: UNDERSTAND"
    print(log_message)
    state['log'].append(log_message)

    common_client = CommonMcpClient()
    atlas_client = AtlasMcpClient()

    parsed_result = common_client.parse_request_text(state['query'])
    entities_result = atlas_client.extract_entities(state['query'])

    state['structured_data'] = {**parsed_result, **entities_result}
    return state

def stage_prepare(state: AgentState) -> AgentState:
    """🛠️ Stage 3: PREPARE - Normalize, enrich, and add flags."""
    log_message = "✅ STAGE: PREPARE"
    print(log_message)
    state['log'].append(log_message)

    common_client = CommonMcpClient()
    atlas_client = AtlasMcpClient()
    
    normalized_result = common_client.normalize_fields(state['ticket_id'])
    enriched_result = atlas_client.enrich_records(state['email'])
    flags_result = common_client.add_flags_calculations(state['priority'], state['query'])

    state['enriched_data'] = {**normalized_result, **enriched_result, **flags_result}
    return state
    
def stage_retrieve(state: AgentState) -> AgentState:
    """📚 Stage 6: RETRIEVE - Search the knowledge base."""
    log_message = "✅ STAGE: RETRIEVE"
    print(log_message)
    state['log'].append(log_message)

    atlas_client = AtlasMcpClient()
    
    kb_result = atlas_client.knowledge_base_search(state['structured_data']['extracted_entities'])
    state['retrieved_kb_article'] = kb_result['retrieved_kb_article']
    return state

def stage_decide(state: AgentState) -> AgentState:
    """⚖️ Stage 7: DECIDE - Evaluate solution and decide next step (non-deterministic)."""
    log_message = "✅ STAGE: DECIDE"
    print(log_message)
    state['log'].append(log_message)

    common_client = CommonMcpClient()
    
    score_result = common_client.solution_evaluation(state['retrieved_kb_article'])
    score = score_result['solution_score']
    
    if score >= 90:
        decision = "Sufficient solution found. Proceed to create response."
        state['decision'] = {"score": score, "outcome": "CREATE_RESPONSE"}
    else:
        decision = "Solution score is low. Escalating to human agent."
        atlas_client = AtlasMcpClient()
        escalation_result = atlas_client.escalation_decision(state['ticket_id'])
        state['decision'] = {"score": score, "outcome": "ESCALATE", **escalation_result}

    print(f"  🧠 Decision Logic: Score is {score}. {decision}")
    state['log'].append(f"  Decision Logic: Score is {score}. {decision}")
    return state

def stage_create(state: AgentState) -> AgentState:
    """✍️ Stage 9: CREATE - Generate a response for the customer."""
    log_message = "✅ STAGE: CREATE"
    print(log_message)
    state['log'].append(log_message)
    
    common_client = CommonMcpClient()
    response_result = common_client.response_generation(
        state['customer_name'],
        state['query'],
        state['retrieved_kb_article']
    )
    state['final_response'] = response_result['generated_response']
    state['final_status'] = "RESOLVED"
    return state

def stage_update(state: AgentState) -> AgentState:
    """🔄 Stage 8: UPDATE - Update the ticket for escalation."""
    log_message = "✅ STAGE: UPDATE"
    print(log_message)
    state['log'].append(log_message)
    
    atlas_client = AtlasMcpClient()
    atlas_client.update_ticket(
        state['ticket_id'],
        status="Escalated",
        assignee="Tier 2 Support"
    )
    state['final_response'] = "This ticket has been escalated for human review."
    state['final_status'] = "ESCALATED"
    return state

def stage_do(state: AgentState) -> AgentState:
    """🏃 Stage 10: DO - Trigger notifications."""
    log_message = "✅ STAGE: DO"
    print(log_message)
    state['log'].append(log_message)
    
    atlas_client = AtlasMcpClient()
    atlas_client.execute_api_calls(state['email'], state['final_response'])
    return state
    
def stage_close(state: AgentState) -> AgentState:
    """✅ Stage 11: CLOSE - Close the ticket if resolved."""
    log_message = "✅ STAGE: CLOSE"
    print(log_message)
    state['log'].append(log_message)

    atlas_client = AtlasMcpClient()
    atlas_client.close_ticket(state['ticket_id'])
    return state

def stage_complete(state: AgentState) -> AgentState:
    """🏁 STAGE: COMPLETE - Final output payload."""
    log_message = "✅ STAGE: COMPLETE - Workflow finished."
    print(log_message)
    state['log'].append(log_message)
    # This is the final node. No further actions.
    return state

# NOTE: STAGES 4 (ASK) and 5 (WAIT) would involve human-in-the-loop interaction.
# They are defined here conceptually but not added to this specific graph flow for a single, non-interactive run.
def stage_ask(state: AgentState): pass
def stage_wait(state: AgentState): pass

# ==============================================================================
# 4. CONDITIONAL LOGIC (for non-deterministic routing)
# ==============================================================================

def route_after_decision(state: AgentState) -> Literal["CREATE", "UPDATE"]:
    """Determines the next path after the DECIDE stage."""
    print("  🚦 Routing based on decision...")
    if state['decision']['outcome'] == "CREATE_RESPONSE":
        print("  🚦 -> Path: CREATE")
        return "CREATE"
    else:
        print("  🚦 -> Path: UPDATE")
        return "UPDATE"

def route_after_do(state: AgentState) -> Literal["CLOSE", "__end__"]:
    """Determines if the ticket should be closed or if the process ends (for escalations)."""
    print("  🚦 Routing after DO...")
    if state['final_status'] == "RESOLVED":
        print("  🚦 -> Path: CLOSE")
        return "CLOSE"
    else: # Escalated tickets are not closed by the agent
        print("  🚦 -> Path: END")
        return END

# ==============================================================================
# 5. GRAPH ASSEMBLY
# ==============================================================================

# Initialize the state graph
workflow = StateGraph(AgentState)

# Add all the nodes (stages)
workflow.add_node("INTAKE", stage_intake)
workflow.add_node("UNDERSTAND", stage_understand)
workflow.add_node("PREPARE", stage_prepare)
workflow.add_node("RETRIEVE", stage_retrieve)
workflow.add_node("DECIDE", stage_decide)
workflow.add_node("CREATE", stage_create)
workflow.add_node("UPDATE", stage_update)
workflow.add_node("DO", stage_do)
workflow.add_node("CLOSE", stage_close)
workflow.add_node("COMPLETE", stage_complete)


# Set the entry point
workflow.set_entry_point("INTAKE")

# Add deterministic edges
workflow.add_edge("INTAKE", "UNDERSTAND")
workflow.add_edge("UNDERSTAND", "PREPARE")
workflow.add_edge("PREPARE", "RETRIEVE")
workflow.add_edge("RETRIEVE", "DECIDE")

# Add conditional edges for the non-deterministic DECIDE stage
workflow.add_conditional_edges(
    "DECIDE",
    route_after_decision,
    {
        "CREATE": "CREATE",
        "UPDATE": "UPDATE",
    }
)

# Continue the flow from the two branches
workflow.add_edge("CREATE", "DO")
workflow.add_edge("UPDATE", "DO")

# Add conditional edge after DO
workflow.add_conditional_edges(
    "DO",
    route_after_do,
    {
        "CLOSE": "CLOSE",
        END: END
    }
)

workflow.add_edge("CLOSE", "COMPLETE")
workflow.add_edge("COMPLETE", END)

# Compile the graph into a runnable app
app = workflow.compile()


# ==============================================================================
# 6. DEMO RUN
# ==============================================================================
if __name__ == "__main__":
    print("🚀 Initiating Langie Support Agent...")
    print("-" * 50)
    
    # --- Sample Input ---
    sample_input = {
        "customer_name": "Alice Wonder",
        "email": "alice.w@example.com",
        "query": "Hi, my Pro-Widget X is showing error code 42. I've tried restarting it but it didn't help. Can you assist?",
        "priority": 4,
        "ticket_id": "TKT-78901",
        "log": [] # Initialize the log
    }
    
    print("📥 Sample Input Payload:")
    print(json.dumps(sample_input, indent=2))
    print("-" * 50)

    # --- Run the Agent ---
    final_state = app.invoke(sample_input)

    print("-" * 50)
    print("✅ Final Structured Payload Output:")
    # Pretty print the final state
    print(json.dumps(final_state, indent=2, default=str))
    print("-" * 50)
    print("Langie Support Agent run complete. 🏁")
