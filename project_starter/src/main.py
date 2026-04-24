import asyncio
from dotenv import load_dotenv
load_dotenv()  # Load .env file securely into OS environment

import structlog
import typer

from src.agent.orchestration import OrchestratorAgent
from src.config import settings
from src.logger import configure_logging

configure_logging()
logger = structlog.get_logger()

app = typer.Typer(help="AI Research Agent CLI")

@app.command()
def research(
    query: str = typer.Argument(..., help="The research query to run."),
    model: str = typer.Option(None, help="LLM model to use (overrides settings)."),
    max_steps: int = typer.Option(settings.max_steps, help="Max ReAct steps."),
):
    """Run the AI research agent on a query. After each report, you can ask follow-up questions."""
    resolved_model = model or settings.model_name
    agent = OrchestratorAgent(model=resolved_model, max_steps=max_steps)

    logger.info("orchestrator_started", query=query, model=resolved_model)
    result = asyncio.run(agent.run(query))

    print("\n" + "="*50)
    print("FINAL REPORT:")
    print("="*50)
    print(result["answer"])
    print("="*50 + "\n")


if __name__ == "__main__":
    app()
