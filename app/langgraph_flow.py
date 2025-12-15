from __future__ import annotations

from typing import Dict, List, Literal, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph


class ConversationState(TypedDict):
    messages: List[BaseMessage]
    route: Literal["tool", "chat"]
    tool_observation: str
    dynamic_system_prompt: str
    prepared_messages: List[BaseMessage]


class KnowledgeBaseTool:
    """A fake internal tool that surfaces structured data."""

    name = "knowledge_base_lookup"

    async def run(self, query: str) -> str:
        catalog = {
            "weather": "Temp 24°C, AQI 18, humidity 40% for San Francisco.",
            "pricing": "Premium automation tier starts at $99/month, includes realtime SLAs.",
            "co2": "Average manufacturing batch emits 14.3kg CO2e; offset via wind credits.",
        }
        for key, value in catalog.items():
            if key in query.lower():
                return f"{key.title()} data → {value}"
        return "No exact knowledge base match; fall back to model reasoning."


class ConversationOrchestrator:
    """LangGraph-powered multi-step router for each user turn."""

    def __init__(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt
        self.tool = KnowledgeBaseTool()
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(ConversationState)

        async def router(state: ConversationState):
            last_user = _find_last_user(state["messages"])
            query = last_user.content if last_user else ""
            contains_tool_keyword = any(k in query.lower() for k in ("weather", "pricing", "co2"))
            route: Literal["tool", "chat"] = "tool" if contains_tool_keyword else "chat"
            return {"route": route}

        async def call_tool(state: ConversationState):
            last_user = _find_last_user(state["messages"])
            observation = await self.tool.run(last_user.content if last_user else "")
            return {"tool_observation": observation, "dynamic_system_prompt": self.system_prompt}

        async def prepare_messages(state: ConversationState):
            prompt = state.get("dynamic_system_prompt") or self.system_prompt
            base: List[BaseMessage] = [SystemMessage(content=prompt)] + state["messages"]
            tool_context = state.get("tool_observation") or ""
            if tool_context:
                base.append(SystemMessage(content=f"Tool context: {tool_context}"))
            return {"prepared_messages": base}

        graph.add_node("router", router)
        graph.add_node("tool", call_tool)
        graph.add_node("prepare", prepare_messages)

        graph.add_edge(START, "router")
        graph.add_conditional_edges(
            "router",
            lambda s: s["route"],
            {
                "tool": "tool",
                "chat": "prepare",
            },
        )
        graph.add_edge("tool", "prepare")
        graph.add_edge("prepare", END)
        return graph.compile()

    async def run_turn(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        state: ConversationState = {
            "messages": messages,
            "route": "chat",
            "tool_observation": "",
            "dynamic_system_prompt": self.system_prompt,
            "prepared_messages": [],
        }
        result = await self._graph.ainvoke(state)
        return result["prepared_messages"]


def _find_last_user(messages: List[BaseMessage]) -> HumanMessage | None:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message
    return None

