import os
import sys
import asyncio
from pathlib import Path
import click
from dotenv import load_dotenv
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelResponse, ToolCallPart

from index import FAQIndex
from tools import web_search

# Setup
load_dotenv()
os.environ["OPENAI_BASE_URL"] = os.environ.get("BASE_URL", "https://openrouter.ai/api/v1")
try:
    os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
except KeyError:
    sys.exit(
        "Error: OPENROUTER_API_KEY is not set. "
        "Copy .env.example to .env and add your OpenRouter API key."
    )

console = Console()

FAQ_PATH = Path(__file__).parent / "data" / "devcolorfaq.txt"
MODEL = os.environ.get("MODEL", "anthropic/claude-opus-4.7")
MAX_HISTORY_MESSAGES = 10

# Agent
agent = Agent(
    f'openai-chat:{MODEL}',
    instructions="""You are a helpful assistant for /dev/color.
                    ALWAYS call search_faq_tool first for any /dev/color question.
                    If (and only if) search_faq_tool returns an empty list,
                    you MUST ask the user for explicit permission before calling
                    web_search_tool. Never call web_search_tool without that
                    confirmation.""",
    deps_type=FAQIndex,
)

@agent.tool
def search_faq_tool(ctx: RunContext[FAQIndex], query: str, top_k: int = 3) -> list[dict]:
    """Search the /dev/color FAQ knowledge base."""
    results = ctx.deps.search(query, top_k)
    return [r.model_dump() for r in results if r.score > 0.5]

@agent.tool_plain
def web_search_tool(query: str) -> list[dict]:
    """Search the web for information not found in the FAQ."""
    return web_search(query)

def print_trace(result):
    for msg in result.all_messages():
        if isinstance(msg, ModelResponse):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    rprint(f"  [bold yellow]🔧 Tool:[/] {part.tool_name}({part.args})")

async def run(verbose: bool = False):
    with console.status("[bold green]Loading FAQ index..."):
        index = FAQIndex(FAQ_PATH.read_text())

    message_history = None
    rprint(Panel("Welcome to the /dev/color FAQ Agent!", title="🤖 Agent", border_style="blue"))

    while True:
        try:
            query = input("\n🤖 Ask me anything (type 'exit' to quit): ")
        except (EOFError, KeyboardInterrupt):
            rprint("\n[bold red]Goodbye![/]")
            break

        if query.lower().strip() in ("exit", "quit"):
            rprint("[bold red]Goodbye![/]")
            break

        with console.status("[bold cyan]Thinking..."):
            result = await agent.run(query, deps=index, message_history=message_history)

        if verbose:
            print_trace(result)

        console.print(Panel(Markdown(result.output), title="💬 Answer", border_style="green"))
        message_history = result.all_messages()

        if len(message_history) >= MAX_HISTORY_MESSAGES:
            rprint(
                f"[bold yellow]⚠ Conversation history reached "
                f"{MAX_HISTORY_MESSAGES} messages — clearing context to keep "
                f"responses focused.[/]"
            )
            message_history = None

@click.command()
@click.option('--verbose', is_flag=True, help='Show agent trace')
def main(verbose):
    asyncio.run(run(verbose))

if __name__ == "__main__":
    main()
