"""
Multi-agent orchestration layer.

Design and implement your own orchestration strategy here.
This file is entirely yours — there is no single correct answer.
"""

from src.agent.base import BaseAgent
from src.agent.prompts import (
    ANALYST_PROMPT,
    FACT_CHECKER_PROMPT,
    PLANNER_PROMPT,
    RESEARCHER_PROMPT,
    WRITER_PROMPT,
)
from src.config import settings


import structlog
from pydantic import BaseModel, Field, field_validator
from litellm import acompletion
from src.observability.observe import observe
from src.tools.registry import registry

logger = structlog.get_logger()

class PlanStep(BaseModel):
    step: int = Field(..., description='Step number')
    task: str = Field(..., description='Task to perform')
    specialist: str = Field(..., description='One of: researcher, analyst, writer')
    depends_on: list[int] = Field(default_factory=list)

    @field_validator('step', mode='before')
    @classmethod
    def convert_step_to_int(cls, v):
        if isinstance(v, dict) and 'step' in v:
            return v['step']
        return v

    @field_validator('depends_on', mode='before')
    @classmethod
    def convert_depends_on_to_ints(cls, v):
        if isinstance(v, list):
            new_list = []
            for item in v:
                if isinstance(item, dict) and 'step' in item:
                    try:
                        new_list.append(int(item['step']))
                    except (ValueError, TypeError):
                        pass
                elif isinstance(item, str):
                    import re
                    digits = re.findall(r'\d+', item)
                    if digits:
                        new_list.append(int(digits[0]))
                else:
                    try:
                        new_list.append(int(item))
                    except (ValueError, TypeError):
                        pass
            return new_list
        return v

class Plan(BaseModel):
    steps: list[PlanStep]

class OrchestratorAgent:
    """
    Planner-first OrchestratorAgent.
    Decomposes the query into ordered steps, then routes to specialized BaseAgents.
    """

    def __init__(self, model: str = None, max_steps: int = 10):
        resolved_model = model or settings.model_name
        self.model = resolved_model
        
        all_tools = registry.get_all_tools()
        
        self.researcher = BaseAgent(
            model=resolved_model,
            max_steps=max_steps,
            agent_name="Researcher",
            system_prompt=RESEARCHER_PROMPT,
            tools=all_tools
        )
        self.analyst = BaseAgent(
            model=resolved_model,
            max_steps=max_steps,
            agent_name="Analyst",
            system_prompt=ANALYST_PROMPT,
            tools=all_tools
        )
        self.writer = BaseAgent(
            model=resolved_model,
            max_steps=max_steps,
            agent_name="Writer",
            system_prompt=WRITER_PROMPT,
            tools=[]
        )

    @observe
    async def create_plan(self, query: str) -> list[dict]:
        instruction = """
        IMPORTANT: You MUST return ONLY valid JSON. No markdown, no explanations.
        Use this exact schema:
        {
          "steps": [
            {
              "step": 1,
              "task": "...",
              "specialist": "researcher",
              "depends_on": []
            }
          ]
        }
        """
        prompt = PLANNER_PROMPT.replace("{query}", query) + "\n" + instruction
        
        try:
            resp = await acompletion(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            content = resp.choices[0].message.content.strip()
            # Clean up markdown code blocks if present
            if content.startswith("```json"):
                content = content.replace("```json", "", 1)
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
            content = content.strip()
            
            plan = Plan.model_validate_json(content)
            return [s.model_dump() for s in plan.steps]
        except Exception as e:
            logger.error("plan_parsing_failed", error=str(e))
            return []

    def _get_context(self, step: dict, results: dict) -> str:
        parts = [f"[Step {d} result]:\n{results[d]}" for d in step.get("depends_on", []) if d in results]
        return "\n\n".join(parts)

    @observe(name="orchestration")
    async def run(self, query: str) -> dict:
        print("INFO   Planning...")
        plan = await self.create_plan(query)
        if not plan:
            return {"answer": "Failed to create a plan.", "metadata": {"total_steps": 0}}
            
        for s in plan:
            print(f"INFO     Step {s['step']} [{s['specialist'].capitalize()}]: {s['task']}")
            
        print("INFO   Executing...")
        results = {}
        total_steps = 0
        
        for step in plan:
            # Fallback: if the model forgot to set depends_on, link it to all previous steps.
            depends_on = step.get("depends_on", [])
            if not depends_on and results:
                step["depends_on"] = list(results.keys())

            context = self._get_context(step, results)
            full_task = step["task"] if not context else f"{step['task']}\n\nContext from previous steps:\n{context}"
            
            specialist = step["specialist"].lower()
            specialist_name = specialist.capitalize()
            print(f"INFO   Running Step {step['step']} [{specialist_name}]...")
            
            if "researcher" in specialist:
                agent = self.researcher
            elif "analyst" in specialist:
                agent = self.analyst
            elif "writer" in specialist:
                agent = self.writer
            else:
                agent = self.researcher # default fallback
                print(f"INFO     (Using Researcher for unknown specialist: {specialist})")
                
            res = await agent.run(full_task)
            results[step["step"]] = res["answer"]
            total_steps += res.get("metadata", {}).get("total_steps", 1)
            
        print("INFO   Synthesizing...")
        final_answer_step = plan[-1]["step"]
        final_answer = results.get(final_answer_step, "No final answer produced.")
            
        return {
            "answer": final_answer,
            "metadata": {
                "total_steps": total_steps,
                "plan": plan
            }
        }
