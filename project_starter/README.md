# AI Agents — Project Starter

Build a production-grade multi-agent research system from scratch.
You are given the observability foundation and a working `BaseAgent` skeleton.
Your job: implement the ReAct loop, then design your own multi-agent pipeline.

---

## Structure

```
project_starter/
├── pyproject.toml           # Dependencies
├── .env.example             # Environment variable template
└── src/
    ├── config.py            # Pydantic settings (complete)
    ├── exceptions.py        # Custom exceptions (complete)
    ├── logger.py            # Structured logging (complete)
    ├── main.py              # Typer CLI (TODO: wire OrchestratorAgent)
    ├── agent/
    │   ├── base.py          # BaseAgent — ReAct loop implemented (complete)
    │   ├── orchestration.py # OrchestratorAgent — entirely TODO (your design)
    │   └── prompts.py       # System prompts for example roles TODO (your design)
    ├── observability/
    │   ├── observe.py       # @observe decorator & langfuse_context stub (complete)
    │   ├── loop_detector.py # LoopDetector (complete)
    │   └── cost_tracker.py  # CostTracker (TODO: log_completion, print_cost_breakdown)
    └── tools/
        ├── registry.py      # ToolRegistry (complete)
        └── search_tool.py   # search_web + read_webpage (complete)
```

---

## Setup

```bash
# 1. Install dependencies
uv pip install -e .

# 2. Configure secrets
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (or another provider key)

# 3. Verify the foundation
uv run python tests/verify_components.py
```

---

## Student Build Order

Work through the remaining TODOs to complete the system.

### Step 1 — `src/observability/cost_tracker.py`
Implement `log_completion()` and `print_cost_breakdown()`. The foundation uses LiteLLM, so your cost tracker should extract usage from the standard response objects.

**Teaches**: token extraction, usage monitoring, cost calculation.
**Verify**: `uv run python tests/verify_components.py` passes all checks.

---

### Step 2 — `src/agent/orchestration.py` → `OrchestratorAgent`
Design and implement your own multi-agent pipeline. You have a working `BaseAgent` that handles reasoning and tool execution; now you must decide how to coordinate them.

| Strategy | Description |
|---|---|
| Sequential chain | Researcher → Analyst → Writer |
| Parallel + synthesize | Researcher ∥ Fact-checker → Writer |
| Retry loop | Re-research if confidence is low |
| Planner-first | Planner breaks query → specialists execute |
| Your own idea | Surprise us! |

**Teaches**: multi-agent design, orchestration patterns, complex async workflows.

---

### Step 3 — `src/main.py` → `research()`
Wire your `OrchestratorAgent` into the Typer CLI so it can be called from the terminal.

**Verify**: `uv run python -m src.main --query "Compare LLMs"` produces a full report.

---

## Quick Reference

```bash
uv pip install -e .                   # install dependencies
uv run python tests/verify_components.py # verify components
uv run python -m src.main "..."       # run query
```

Available prompts in `src/agent/prompts.py`:
- `DEFAULT_SYSTEM_PROMPT`
- `RESEARCHER_PROMPT`
- `ANALYST_PROMPT`
- `WRITER_PROMPT`
- `FACT_CHECKER_PROMPT`
- `PLANNER_PROMPT`
