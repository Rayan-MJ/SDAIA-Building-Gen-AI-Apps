import logging
from dataclasses import dataclass, field
from litellm import completion_cost

logger = logging.getLogger(__name__)

@dataclass
class StepCost:
    step_number: int
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    is_tool_call: bool = False

@dataclass
class QueryCost:
    query: str
    steps: list[StepCost] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def add_step(self, step: StepCost):
        self.steps.append(step)
        self.total_cost_usd += step.cost_usd
        self.total_input_tokens += step.input_tokens
        self.total_output_tokens += step.output_tokens

class CostTracker:
    """
    Tracks costs across agent executions.
    """
    def __init__(self):
        self.queries: list[QueryCost] = []
        self._current_query: QueryCost | None = None

    def start_query(self, query: str):
        self._current_query = QueryCost(query=query)

    def log_completion(self, step_number: int, response, is_tool_call: bool = False):
        """
        Log a completion response's cost.
        """
        # TODO: Implement this method
        # 1. Check if _current_query exists
        # 2. Extract usage stats from response
        # 3. Calculate cost (use litellm.completion_cost or fallback)
        # 4. create StepCost and add to query
        if not self._current_query:
            logger.warning("No active query to log completion for")
            return
        try:
            cost = completion_cost(completion_response=response)
        except Exception as e:
            logger.warning(f"Could not calculate cost: {e}")
            cost = 0.0
        model = getattr(response, "model", "unknown")
        
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", 0)
            output_tokens = getattr(usage, "completion_tokens", 0)
        else:
            input_tokens = 0
            output_tokens = 0
        step_cost = StepCost(
            step_number=step_number,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            is_tool_call=is_tool_call
        )
        self._current_query.add_step(step_cost)

    def end_query(self):
        if self._current_query:
            self.queries.append(self._current_query)
            self._current_query = None

    def print_cost_breakdown(self):
        print("\n" + "="*40)
        print("COST BREAKDOWN")
        print("="*40)
        
        grand_total = 0.0
        total_in_tokens = 0
        total_out_tokens = 0
        
        for i, q in enumerate(self.queries, 1):
            print(f"Query {i}: {q.query}")
            print(f"Total Cost: ${q.total_cost_usd:.6f}")
            print(f"Total Input Tokens: {q.total_input_tokens}")
            print(f"Total Output Tokens: {q.total_output_tokens}")
            print("-" * 20)
            
            for step in q.steps:
                tool_str = " (Tool Call)" if step.is_tool_call else ""
                print(f"  Step {step.step_number}{tool_str} - Model: {step.model}")
                print(f"    Tokens: {step.input_tokens} In / {step.output_tokens} Out")
                print(f"    Cost: ${step.cost_usd:.6f}")
                
            grand_total += q.total_cost_usd
            total_in_tokens += q.total_input_tokens
            total_out_tokens += q.total_output_tokens
            print()
            
        print("="*40)
        print(f"GRAND TOTAL COST: ${grand_total:.6f}")
        print(f"GRAND TOTAL TOKENS: {total_in_tokens} In / {total_out_tokens} Out")
        print("="*40 + "\n")

