#!/usr/bin/env python3
"""
setup_01_salesforce_mcp.py
Step 1 of 3 — Set up the Salesforce DX MCP server for Claude Code.

The Salesforce DX MCP gives Claude Code direct access to your org:
  - Run SOQL queries
  - Deploy and retrieve metadata
  - Create scratch orgs, run tests, analyze code quality
  - And 80+ other Salesforce development tools

Run: python3 setup_01_salesforce_mcp.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

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


def check_command(cmd, label):
    success, out, _ = run(f"{cmd} --version")
    if success:
        version = out.splitlines()[0] if out else "(version unknown)"
        ok(f"{label}: {version}")
        return True
    else:
        fail(f"{label} not found")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    banner("Salesforce Demo Builder — Step 1 of 3\nSalesforce DX MCP Setup")
    print("""
  This script sets up the Salesforce DX MCP server, which gives
  Claude Code direct access to your Salesforce org.

  It will:
    1. Verify your prerequisites (Node.js, Salesforce CLI)
    2. Authenticate Claude Code with your org
    3. Write the MCP server config to your project
    4. Verify the connection works

  You only need to run this once per project.
""")

    # ── STEP 1: Check prerequisites ──────────────────────────────────────────
    step(1, 4, "Checking prerequisites")

    node_ok = check_command("node", "Node.js")
    npm_ok  = check_command("npm", "npm")
    sf_ok   = check_command("sf", "Salesforce CLI")

    if not node_ok or not npm_ok:
        print("""
  Node.js and npm are required. Install from:
    https://nodejs.org  (LTS version recommended)

  Then run this script again.
""")
        sys.exit(1)

    if not sf_ok:
        print("""
  Salesforce CLI is required. Install with:
    npm install -g @salesforce/cli

  Then run this script again.
""")
        sys.exit(1)

    # Check for Claude Code
    claude_ok = check_command("claude", "Claude Code")
    if not claude_ok:
        print("""
  Claude Code CLI is required. Install with:
    npm install -g @anthropic-ai/claude-code

  Then run this script again.
""")
        sys.exit(1)

    # ── STEP 2: Authenticate with Salesforce org ─────────────────────────────
    step(2, 4, "Authenticate with your Salesforce org")

    # Check for existing orgs
    success, out, _ = run("sf org list --json")
    existing_orgs = []
    if success and out:
        try:
            data = json.loads(out)
            orgs = data.get("result", {})
            for category in ("nonScratchOrgs", "scratchOrgs", "sandboxes"):
                for o in orgs.get(category, []):
                    alias = o.get("alias", "")
                    username = o.get("username", "")
                    existing_orgs.append((alias, username))
        except Exception:
            pass

    if existing_orgs:
        print(f"\n  You have {len(existing_orgs)} org(s) already authorized:\n")
        for i, (alias, username) in enumerate(existing_orgs, 1):
            label = f"{alias} ({username})" if alias else username
            print(f"    {i}. {label}")
        print()
        choice = input("  Use an existing org? Enter number, or press Enter to log into a new one: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(existing_orgs):
            idx = int(choice) - 1
            chosen_alias, chosen_username = existing_orgs[idx]
            org_alias = chosen_alias or chosen_username
            ok(f"Using existing org: {org_alias}")
        else:
            org_alias = _login_new_org()
    else:
        print("  No authorized orgs found. Let's log in to your org.")
        org_alias = _login_new_org()

    # Verify the org is accessible
    print(f"\n  Verifying org '{org_alias}'...")
    success, out, err = run(f"sf org display --target-org {org_alias} --json")
    if not success:
        fail(f"Could not connect to org '{org_alias}': {err}")
        print("  Run: sf org login web --alias <your-alias>  then try again.")
        sys.exit(1)

    try:
        result = json.loads(out).get("result", {})
        instance_url = result.get("instanceUrl", "")
        username = result.get("username", "")
        ok(f"Connected to: {instance_url}")
        ok(f"Username: {username}")
    except Exception:
        ok(f"Org '{org_alias}' is accessible")

    # ── STEP 3: Write .mcp.json ───────────────────────────────────────────────
    step(3, 4, "Configure the Salesforce DX MCP server")

    project_root = Path.cwd()
    mcp_path = project_root / ".mcp.json"

    existing_config = {}
    if mcp_path.exists():
        try:
            existing_config = json.loads(mcp_path.read_text())
            info(f"Found existing .mcp.json — will merge")
        except Exception:
            warn("Existing .mcp.json could not be parsed — will overwrite")

    servers = existing_config.get("mcpServers", {})
    servers["salesforce-dx"] = {
        "command": "npx",
        "args": ["@salesforce/mcp", "--target-org", org_alias]
    }
    existing_config["mcpServers"] = servers

    mcp_path.write_text(json.dumps(existing_config, indent=2) + "\n")
    ok(f"Written: {mcp_path}")

    # Write a project-level settings file with sensible permission allowances
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
        "mcp__salesforce-dx__get_username",
        "mcp__salesforce-dx__list_all_orgs",
        "mcp__salesforce-dx__run_soql_query",
        "mcp__salesforce-dx__deploy_metadata",
        "mcp__salesforce-dx__retrieve_metadata",
        f"Bash(sf org *)",
        f"Bash(sf project deploy *)",
        f"Bash(sf project retrieve *)",
        f"Bash(sf data *)",
    ]
    for p in new_perms:
        if p not in allowed:
            allowed.append(p)

    perms["allow"] = allowed
    existing_settings["permissions"] = perms
    existing_settings["enableAllProjectMcpServers"] = True

    settings_path.write_text(json.dumps(existing_settings, indent=2) + "\n")
    ok(f"Written: {settings_path}")

    # ── STEP 4: Verify ───────────────────────────────────────────────────────
    step(4, 4, "Verify the setup")

    print("""
  To verify the Salesforce DX MCP is working:

    1. Restart Claude Code (the MCP server loads at startup):
         claude

    2. In Claude Code, run:
         /mcp

       You should see 'salesforce-dx' listed as an active server with
       tools like run_soql_query, deploy_metadata, etc.

    3. Test it by asking Claude:
         "What is my current Salesforce org username?"

  If the server doesn't appear, check that .mcp.json is in your
  project root and that Node.js can run 'npx @salesforce/mcp'.
""")

    banner("Step 1 Complete")
    print(f"""
  Salesforce DX MCP is configured for org: {org_alias}

  Files written:
    .mcp.json                     MCP server registration
    .claude/settings.local.json   Permission allowances

  Next: run setup_02_tableau_next_mcp.py to connect
  Claude Code to Tableau Next analytics.
""")


def _login_new_org():
    alias = input("  Enter an alias for this org (e.g. MyDemoOrg): ").strip()
    if not alias:
        alias = "DemoOrg"

    print(f"\n  Opening browser for Salesforce login...")
    info("Log in with your org credentials, then return here.")
    print()

    success, out, err = run(f"sf org login web --alias {alias}", capture=False)
    if not success:
        fail(f"Login failed: {err}")
        sys.exit(1)

    ok(f"Logged in as: {alias}")
    return alias


if __name__ == "__main__":
    main()
