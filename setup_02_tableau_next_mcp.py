#!/usr/bin/env python3
"""
setup_02_tableau_next_mcp.py
Step 2 of 3 — Set up the Tableau Next MCP server for Claude Code.

The Tableau Next MCP is a Salesforce-hosted server that gives Claude Code
direct access to your Tableau Next analytics:
  - Discover and query semantic data models (SDMs)
  - Run natural-language analysis against your data
  - List and inspect dashboards, workspaces, and visualizations
  - Build analytics components from real data shapes

MCP Server URL: https://api.salesforce.com/platform/mcp/v1/analytics/tableau-next

Run: python3 setup_02_tableau_next_mcp.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

TABLEAU_NEXT_MCP_URL = "https://api.salesforce.com/platform/mcp/v1/analytics/tableau-next"
TABLEAU_NEXT_MCP_NAME = "tableau-next"

def banner(title):
    width = 64
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")


def step(n, total, text):
    print(f"\n[Step {n}/{total}] {text}")
    print("─" * 50)


def ok(msg):    print(f"  OK  {msg}")
def warn(msg):  print(f"  !!  {msg}")
def fail(msg):  print(f"  XX  {msg}")
def info(msg):  print(f"       {msg}")
def pause(msg="Press Enter to continue..."): input(f"\n  >>  {msg}")


def run(cmd, capture=True):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=capture, text=True, timeout=30)
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "timed out"
    except Exception as e:
        return False, "", str(e)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    banner("Salesforce Demo Builder — Step 2 of 3\nTableau Next MCP Setup")
    print(f"""
  This script connects Claude Code to the Tableau Next MCP server —
  a Salesforce-hosted endpoint that gives Claude direct access to
  your analytics data and semantic models.

  MCP Server URL:
    {TABLEAU_NEXT_MCP_URL}

  What you'll need:
    - An External Client App in your Salesforce org (we'll guide you)
    - The Consumer Key from that app
    - Claude Code CLI installed

  You only need to run this once. The MCP registration is global
  (not per-project), so it works across all your demo projects.
""")

    # ── STEP 1: Check prerequisites ──────────────────────────────────────────
    step(1, 4, "Checking prerequisites")

    success, out, _ = run("claude --version")
    if not success:
        fail("Claude Code CLI not found")
        print("""
  Install Claude Code:
    npm install -g @anthropic-ai/claude-code

  Then run this script again.
""")
        sys.exit(1)
    ok(f"Claude Code: {out.splitlines()[0]}")

    success, out, _ = run("sf --version")
    if not success:
        warn("Salesforce CLI not found — needed to verify org settings")
        info("Install: npm install -g @salesforce/cli")
    else:
        ok(f"Salesforce CLI: {out.splitlines()[0]}")

    # ── STEP 2: Enable Tableau Next MCP in your org (admin step) ─────────────
    step(2, 4, "Enable Tableau Next MCP Server in your org (admin)")

    print("""
  Before connecting Claude Code, an org admin must enable the
  Tableau Next MCP server. If you're the admin, do this now.
  If someone else manages your org, ask them to complete these steps.

  ┌─────────────────────────────────────────────────────────┐
  │  IN YOUR SALESFORCE ORG:                                │
  │                                                         │
  │  1. Open your Tableau Next environment                  │
  │                                                         │
  │  2. Navigate to:                                        │
  │       Settings → Integrations → MCP Servers             │
  │     (or search "MCP" in Setup)                          │
  │                                                         │
  │  3. Find "tableau-next" and toggle it ON                │
  │                                                         │
  │  4. Confirm the Server Status shows "Active"            │
  │                                                         │
  │  The Server URL will show as:                           │
  │    https://api.salesforce.com/platform/mcp/             │
  │    v1/analytics/tableau-next                            │
  └─────────────────────────────────────────────────────────┘

  Salesforce Help reference:
    help.salesforce.com → analytics.tua_data_sdm_mcp_enable.htm
""")

    pause("Press Enter once the Tableau Next MCP server shows Active...")

    # ── STEP 3: Create External Client App ───────────────────────────────────
    step(3, 4, "Create an External Client App and get your Consumer Key")

    print("""
  Claude Code authenticates with Tableau Next MCP via OAuth 2.0
  using an External Client App (not a Connected App).

  ┌─────────────────────────────────────────────────────────┐
  │  IN SALESFORCE SETUP:                                   │
  │                                                         │
  │  1. Go to Setup → search "External Client App Manager"  │
  │     (under Apps → External Client Apps)                 │
  │                                                         │
  │  2. Click "New External Client App"                     │
  │                                                         │
  │  3. Fill in:                                            │
  │       App Name:   Claude Code MCP                       │
  │       API Name:   Claude_Code_MCP                       │
  │       Contact Email: your email                         │
  │                                                         │
  │  4. Under OAuth Settings:                               │
  │       Callback URL:                                     │
  │         http://localhost:8080/callback                  │
  │                                                         │
  │  5. Add these two OAuth Scopes:                         │
  │       • Perform requests at any time                    │
  │           (refresh_token, offline_access)               │
  │       • Access Salesforce hosted MCP servers            │
  │           (mcp_server_access)                           │
  │                                                         │
  │  6. Click Save                                          │
  │                                                         │
  │  7. Click "Consumer Key and Secret" to reveal the key   │
  │     Copy the Consumer Key — you'll paste it below       │
  └─────────────────────────────────────────────────────────┘

  Note: External Client Apps may take 2-5 minutes to propagate
  after saving. If the OAuth step fails, wait a few minutes and
  re-run this script.
""")

    consumer_key = ""
    while not consumer_key:
        consumer_key = input("  Paste your Consumer Key here: ").strip()
        if not consumer_key:
            print("  Consumer Key is required. Check Setup → External Client App Manager.")

    # ── STEP 4: Register with Claude Code ────────────────────────────────────
    step(4, 4, "Register the Tableau Next MCP server with Claude Code")

    # Check if already registered
    success, out, _ = run("claude mcp list")
    already_registered = TABLEAU_NEXT_MCP_NAME in out if success else False

    if already_registered:
        warn(f"'{TABLEAU_NEXT_MCP_NAME}' is already registered with Claude Code.")
        choice = input("  Re-register with the new Consumer Key? (yes/no) [yes]: ").strip().lower()
        if choice not in ("yes", "y", ""):
            print("  Keeping existing registration.")
        else:
            # Remove existing and re-add
            run(f"claude mcp remove {TABLEAU_NEXT_MCP_NAME}", capture=False)
            _register_mcp(consumer_key)
    else:
        _register_mcp(consumer_key)

    # Update project settings to allow Tableau Next MCP tool calls
    project_root = Path.cwd()
    claude_dir = project_root / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.local.json"

    existing_settings = {}
    if settings_path.exists():
        try:
            existing_settings = json.loads(settings_path.read_text())
        except Exception:
            pass

    perms = existing_settings.get("permissions", {})
    allowed = perms.get("allow", [])

    new_perms = [
        "mcp__tableau-next__list_semantic_models",
        "mcp__tableau-next__list_workspaces",
        "mcp__tableau-next__list_dashboards",
        "mcp__tableau-next__analyze_data",
        "mcp__tableau-next__get_semantic_model",
    ]
    for p in new_perms:
        if p not in allowed:
            allowed.append(p)

    perms["allow"] = allowed
    existing_settings["permissions"] = perms
    settings_path.write_text(json.dumps(existing_settings, indent=2) + "\n")
    ok(f"Updated: {settings_path}")

    # ── Print verification instructions ──────────────────────────────────────
    print("""
  The MCP server is registered. Now authenticate and verify:

    1. Restart Claude Code:
         claude

    2. Run the MCP auth command:
         /mcp

       Claude will prompt you to authenticate — click the link,
       log in with your Salesforce credentials, and click Allow.

    3. Verify by asking Claude:
         "List my Tableau Next semantic models"

       You should see models from your org listed in the response.

  Troubleshooting:
    - "MCP server not connecting" → check that Tableau Next MCP is
      toggled ON in your org's Settings → Integrations → MCP Servers
    - "OAuth fails" → wait 5 minutes for the External Client App to
      propagate, then re-run this script
    - "Tools not appearing" → run /mcp to re-authenticate
    - "Session expires" → Tableau Next MCP requires re-auth each new
      Claude Code session — run /mcp at the start of each session
    - "Permission denied on a model" → ask your org admin to grant
      your user access to the semantic model in Tableau Next
""")

    banner("Step 2 Complete")
    print(f"""
  Tableau Next MCP is registered with Claude Code.

  Consumer Key used: {consumer_key[:8]}...{consumer_key[-4:]}
  MCP URL: {TABLEAU_NEXT_MCP_URL}

  Next: run setup_03_new_demo.py to create your first
  demo project with a pre-configured CLAUDE.md.
""")


def _register_mcp(consumer_key):
    cmd = (
        f"claude mcp add {TABLEAU_NEXT_MCP_NAME} "
        f"{TABLEAU_NEXT_MCP_URL} "
        f"--transport http "
        f"--callback-port 8080 "
        f"--client-id {consumer_key}"
    )
    print(f"\n  Registering Tableau Next MCP with Claude Code...")
    info(f"Running: claude mcp add {TABLEAU_NEXT_MCP_NAME} <url> --transport http --callback-port 8080 --client-id <key>")
    print()

    success, out, err = run(cmd, capture=False)
    if not success and err:
        warn(f"Registration may have failed: {err}")
        info("You can register manually by running:")
        info(f"  claude mcp add {TABLEAU_NEXT_MCP_NAME} \\")
        info(f"    {TABLEAU_NEXT_MCP_URL} \\")
        info(f"    --transport http --callback-port 8080 \\")
        info(f"    --client-id <your-consumer-key>")
    else:
        ok(f"Registered '{TABLEAU_NEXT_MCP_NAME}' with Claude Code")


if __name__ == "__main__":
    main()
