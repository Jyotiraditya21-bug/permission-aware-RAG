import json
import time
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Permission-Aware RAG CLI (prag)")
console = Console()

CONFIG_DIR = Path.home() / ".prag"
CONFIG_FILE = CONFIG_DIR / "config.json"

class State:
    api_url: str = "http://localhost:8000"

state = State()

@app.callback()
def main(api_url: str = typer.Option("http://localhost:8000", help="Base URL of the RAG API")):
    state.api_url = api_url.rstrip("/")

def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

@app.command()
def login(
    user: str = typer.Option(..., "--user", "-u", help="User ID for DEV-ONLY auth header"),
    tenant: str = typer.Option(..., "--tenant", "-t", help="Tenant ID for DEV-ONLY auth header")
):
    """
    Log in by storing DEV-ONLY auth headers locally.
    """
    config = load_config()
    config["user_id"] = user
    config["tenant_id"] = tenant
    save_config(config)
    console.print(f"[green]Successfully logged in as user '{user}' for tenant '{tenant}'[/green]")
    console.print("[yellow]Note: This uses DEV-ONLY header auth. In production, this would exchange credentials for a JWT.[/yellow]")

@app.command()
def whoami():
    """
    Show the currently logged-in demo user and tenant.
    """
    config = load_config()
    user = config.get("user_id")
    tenant = config.get("tenant_id")
    if user and tenant:
        console.print(f"Logged in as user: [bold cyan]{user}[/bold cyan]")
        console.print(f"Tenant: [bold cyan]{tenant}[/bold cyan]")
    else:
        console.print("[yellow]Not logged in. Use `prag login` first.[/yellow]")

@app.command()
def ask(
    question: str = typer.Argument(..., help="The query to send to the RAG platform"),
    raw: bool = typer.Option(False, "--raw", help="Print the raw JSON response instead of pretty-printing")
):
    """
    Ask a question to the RAG platform.
    """
    config = load_config()
    user = config.get("user_id")
    tenant = config.get("tenant_id")
    
    if not user or not tenant:
        console.print("[red]Error: Not logged in. Please run `prag login` first.[/red]")
        raise typer.Exit(1)
        
    headers = {
        "Content-Type": "application/json",
        "X-User-Id": user,
        "X-Tenant-Id": tenant
    }
    payload = {"query": question}
    
    start_time = time.time()
    try:
        response = httpx.post(f"{state.api_url}/query", json=payload, headers=headers, timeout=30.0)
    except httpx.ConnectError:
        console.print(f"[red]Error: Could not connect to API at {state.api_url}. Is it running?[/red]")
        raise typer.Exit(1)
    except httpx.TimeoutException:
        console.print(f"[red]Error: Request to {state.api_url} timed out.[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: An unexpected error occurred: {str(e)}[/red]")
        raise typer.Exit(1)
        
    latency_ms = int((time.time() - start_time) * 1000)
    
    if response.status_code in (401, 403):
        detail = "Unauthorized"
        try:
            detail = response.json().get("detail", detail)
        except Exception:
            pass
        console.print(f"[red]Access denied: {detail} ({response.status_code})[/red]")
        raise typer.Exit(1)
        
    try:
        data = response.json()
    except Exception:
        console.print("[red]Error: Received malformed JSON from API.[/red]")
        console.print(response.text)
        raise typer.Exit(1)
        
    if not response.is_success:
        error_detail = data.get("detail", response.text)
        console.print(f"[red]API Error ({response.status_code}): {error_detail}[/red]")
        raise typer.Exit(1)
        
    if raw:
        print(json.dumps(data, indent=2))
        return

    # Pretty print
    status = data.get("status", "unknown")
    status_color = "green" if status == "grounded" else ("yellow" if status == "abstained" else "blue")
    
    console.print(Panel.fit(
        data.get("text", ""),
        title=f"Answer ([{status_color}]{status}[/{status_color}])",
        border_style="cyan"
    ))
    
    citations = data.get("citations", [])
    if citations:
        table = Table(title="Sources", show_header=True, header_style="bold magenta")
        table.add_column("Claim")
        table.add_column("Chunk IDs")
        
        for c in citations:
            claim = c.get("claim", "")
            chunk_ids = ", ".join(c.get("chunk_ids", []))
            table.add_row(claim, chunk_ids)
            
        console.print(table)
        
    console.print(f"\n[dim]Latency: {latency_ms}ms | Route: {data.get('route', 'N/A')} | Trace: {data.get('trace_id', 'N/A')}[/dim]")

if __name__ == "__main__":
    app()
