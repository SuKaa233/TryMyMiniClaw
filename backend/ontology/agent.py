from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from backend.tools.ontology_tools import ontology_tools
import os

class OntologyAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def get_ontology_system_prompt() -> str:
    return """You are an Ontology Assistant. Your goal is to help users manage Project, Team, Developer, Requirement, and Task entities.

Your Capabilities:
1. **Understanding Graph Structure**: You have access to the 'get_graph_schema' tool. Use it to understand the node types and relationships in the database.
2. **Knowledge Retrieval**: You have access to the 'search_knowledge_graph' tool. Use it to find existing entities when the user asks about them or when you need to link new entities to existing ones.
3. **Entity Creation**: You can propose creating new entities using the 'propose_create_...' tools.
4. **MySQL Sync**: You can sync a MySQL database into Neo4j using the 'import_mysql_to_neo4j' tool when the user asks to import or sync MySQL.

Guidelines:
- **Proactive Schema Check**: At the start of a conversation or when you are unsure about the data model, call 'get_graph_schema' to refresh your understanding.
- **Contextual Search**: If the user refers to an existing entity (e.g., "Add a task to Project Alpha"), use 'search_knowledge_graph' to find "Project Alpha" first to confirm it exists and get its ID/details.
- **Form Proposal**: When the user wants to create an entity, DO NOT ask for every single detail if it's not provided. Instead, use the 'propose_create_...' tools IMMEDIATELY with whatever information you have. The user will be presented with a form to fill in the rest.
- **Avoid Redundant Questions**: If the user says "Create a project", just call 'propose_create_project(name="")'. Don't ask "What is the name?". The form handles that.

Example:
- User: "Create a project named Alpha" -> Call propose_create_project(name="Alpha")
- User: "Add a task to fix bugs" -> Call propose_create_task(name="Fix bugs")
- User: "What projects do we have?" -> Call search_knowledge_graph(query="Project")
- User: "Sync my MySQL database" -> Call import_mysql_to_neo4j()

- **Table Output**: When the user asks for a list of entities (e.g., "List all projects", "Show me the tasks"), format your response as a Markdown table.

Do not execute the creation directly. Always use the 'propose_' tools to show the form.
"""

def create_ontology_graph():
    # Model
    model_name = os.getenv("MODEL_NAME", "moonshot-v1-8k")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.moonshot.cn/v1")
    api_key = os.getenv("OPENAI_API_KEY")

    model = ChatOpenAI(
        model_name=model_name,
        temperature=0,
        base_url=base_url,
        api_key=api_key
    )

    # Bind tools
    model = model.bind_tools(ontology_tools)

    # Node Logic
    def agent_node(state: OntologyAgentState):
        messages = state["messages"]
        
        # We rely on the router to inject the FULL graph context as a SystemMessage for the first turn.
        # But we still want to keep the base system prompt instructions.
        
        # Check if we already have a SystemMessage with "Here is the COMPLETE current state"
        has_context = False
        for m in messages:
            if isinstance(m, SystemMessage) and "COMPLETE current state" in m.content:
                has_context = True
                break
        
        base_prompt = get_ontology_system_prompt()
        
        # If no full context (e.g. second turn, or router failed), we can at least inject schema
        if not has_context:
            from backend.tools.ontology_tools import get_graph_schema
            schema_desc = get_graph_schema.invoke({})
            base_prompt += f"\n\nCurrent Database Schema:\n{schema_desc}"
        
        # Always prepend the base instruction prompt.
        # However, since we are using ChatOpenAI, we should ideally have only one SystemMessage at the start.
        # Let's just create a new list where our base prompt is first.
        
        # Filter out any existing "Instruction" system messages to avoid duplication,
        # but KEEP the "Context" system message injected by the router.
        
        final_messages = []
        # Add base instructions first
        final_messages.append(SystemMessage(content=base_prompt))
        
        for m in messages:
            # If it's a SystemMessage with context, keep it.
            if isinstance(m, SystemMessage) and "COMPLETE current state" in m.content:
                final_messages.append(m)
            elif not isinstance(m, SystemMessage):
                final_messages.append(m)
        
        response = model.invoke(final_messages)
        return {"messages": [response]}

    # Graph
    workflow = StateGraph(OntologyAgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(ontology_tools))

    workflow.set_entry_point("agent")

    def should_continue(state: OntologyAgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile()

ontology_graph = create_ontology_graph()
