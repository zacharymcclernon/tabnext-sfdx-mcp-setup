#!/usr/bin/env python3
"""
setup_03_new_demo.py
Step 3 of 3 — Create a new Salesforce + Tableau Next demo project.

This script collects your demo context, creates a project directory,
and generates a CLAUDE.md that gives Claude Code full architectural
context for Tableau Next + Salesforce development — so it builds
correctly from the first prompt.

Run: python3 setup_03_new_demo.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = SCRIPT_DIR / "templates"

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


def ask(prompt, default=None, required=True):
    suffix = f" [{default}]" if default else ""
    while True:
        val = input(f"\n  {prompt}{suffix}: ").strip()
        if val:
            return val
        if default:
            return default
        if not required:
            return ""
        print("  This field is required.")


def choose(prompt, options):
    print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    while True:
        val = input("\n  Enter number (or type your own): ").strip()
        if val.isdigit() and 1 <= int(val) <= len(options):
            return options[int(val) - 1]
        elif val:
            return val
        print("  Please enter a number or type a custom value.")


def run(cmd, capture=True):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=capture, text=True, timeout=30)
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return False, "", str(e)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    banner("Salesforce Demo Builder — Step 3 of 3\nNew Demo Project Setup")
    print("""
  This script creates a new demo project directory with:
    - CLAUDE.md  (architectural context for Claude Code)
    - .mcp.json  (Salesforce DX MCP registration)
    - .claude/settings.local.json  (permission allowances)
    - scripts/   (Tableau Next build script templates)
    - A starter prompt to kick off building with Claude

  Answer a few questions about your demo and the project
  will be ready to open in Claude Code.
""")

    # ── STEP 1: Demo context ─────────────────────────────────────────────────
    step(1, 5, "Tell me about your demo")

    demo_name = ask("Demo project name (used as folder name, no spaces)", default="MyDemo")
    demo_name = demo_name.replace(" ", "_")

    industry = choose(
        "What industry is this demo for?",
        [
            "Financial Services",
            "Healthcare & Life Sciences",
            "Retail & Consumer Goods",
            "Manufacturing",
            "Technology",
            "Media & Entertainment",
            "Public Sector",
            "Nonprofit",
        ]
    )

    persona = choose(
        "Who is the primary persona this demo is built for?",
        [
            "Sales Representative",
            "Account Executive",
            "Customer Success Manager",
            "Sales Leader / VP",
            "Marketing Manager",
            "Operations / Ops Leader",
            "Service Agent",
            "C-Suite / Executive",
        ]
    )

    print(f"""
  Describe the business story or 'aha moment' you want to demo.
  Example: "Show a Sales VP how AI surfaces at-risk deals before
  they slip, and prescribes the right action at the right time."
""")
    story = ask("Your demo story (1-2 sentences)")

    # ── STEP 2: Salesforce org ───────────────────────────────────────────────
    step(2, 5, "Select your Salesforce org")

    success, out, _ = run("sf org list --json")
    orgs = []
    if success and out:
        try:
            data = json.loads(out)
            result = data.get("result", {})
            for category in ("nonScratchOrgs", "scratchOrgs", "sandboxes"):
                for o in result.get(category, []):
                    alias = o.get("alias", "")
                    username = o.get("username", "")
                    if alias or username:
                        orgs.append((alias, username))
        except Exception:
            pass

    if orgs:
        print(f"\n  Authorized orgs:\n")
        labels = []
        for alias, username in orgs:
            label = f"{alias}  ({username})" if alias else username
            labels.append(label)
            print(f"    - {label}")

        org_input = ask("Enter org alias or username to use")
        org_alias = org_input.strip()
    else:
        warn("No authorized orgs found. You can set the alias manually.")
        org_alias = ask("Org alias (you can update this in CLAUDE.md later)", default="MyDemoOrg")

    # ── STEP 3: Create project directory ────────────────────────────────────
    step(3, 5, "Creating project directory")

    project_dir = Path.cwd() / demo_name
    if project_dir.exists():
        warn(f"Directory '{demo_name}' already exists.")
        choice = input("  Overwrite it? (yes/no) [no]: ").strip().lower()
        if choice not in ("yes", "y"):
            print("  Cancelled. Choose a different demo name and run again.")
            sys.exit(0)
        shutil.rmtree(project_dir)

    project_dir.mkdir(parents=True)
    (project_dir / "force-app" / "main" / "default" / "lwc").mkdir(parents=True)
    (project_dir / "force-app" / "main" / "default" / "classes").mkdir(parents=True)
    (project_dir / "scripts").mkdir(parents=True)
    (project_dir / ".claude").mkdir(parents=True)

    ok(f"Created: {project_dir}")

    # ── STEP 4: Generate project files ──────────────────────────────────────
    step(4, 5, "Generating project files")

    # CLAUDE.md — stamp the template
    template_path = TEMPLATE_DIR / "CLAUDE.md"
    if not template_path.exists():
        fail(f"Template not found at {template_path}")
        fail("Make sure the 'templates/' directory is next to this script.")
        sys.exit(1)

    claude_md = template_path.read_text()
    claude_md = claude_md.replace("{{DEMO_NAME}}", demo_name)
    claude_md = claude_md.replace("{{INDUSTRY}}", industry)
    claude_md = claude_md.replace("{{PERSONA}}", persona)
    claude_md = claude_md.replace("{{STORY}}", story)
    claude_md = claude_md.replace("{{ORG_ALIAS}}", org_alias)

    (project_dir / "CLAUDE.md").write_text(claude_md)
    ok("Generated: CLAUDE.md")

    # .mcp.json — Salesforce DX MCP
    mcp_config = {
        "mcpServers": {
            "salesforce-dx": {
                "command": "npx",
                "args": ["@salesforce/mcp", "--target-org", org_alias]
            }
        }
    }
    (project_dir / ".mcp.json").write_text(json.dumps(mcp_config, indent=2) + "\n")
    ok("Generated: .mcp.json")

    # .claude/settings.local.json — permission allowances
    settings = {
        "permissions": {
            "allow": [
                "mcp__salesforce-dx__get_username",
                "mcp__salesforce-dx__list_all_orgs",
                "mcp__salesforce-dx__run_soql_query",
                "mcp__salesforce-dx__deploy_metadata",
                "mcp__salesforce-dx__retrieve_metadata",
                "mcp__tableau-next__list_semantic_models",
                "mcp__tableau-next__list_workspaces",
                "mcp__tableau-next__list_dashboards",
                "mcp__tableau-next__analyze_data",
                "mcp__tableau-next__get_semantic_model",
                "Bash(sf org *)",
                "Bash(sf project deploy *)",
                "Bash(sf project retrieve *)",
                "Bash(sf data *)",
                "Bash(python3 scripts/*.py*)",
                "Bash(pip install *)",
                "Bash(pip3 install *)",
            ]
        },
        "enableAllProjectMcpServers": True,
        "enabledMcpjsonServers": ["salesforce-dx"]
    }
    settings_path = project_dir / ".claude" / "settings.local.json"
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    ok("Generated: .claude/settings.local.json")

    # sfdx-project.json
    sfdx = {
        "packageDirectories": [{"path": "force-app", "default": True}],
        "name": demo_name,
        "namespace": "",
        "sfdcLoginUrl": "https://login.salesforce.com",
        "sourceApiVersion": "66.0"
    }
    (project_dir / "sfdx-project.json").write_text(json.dumps(sfdx, indent=2) + "\n")
    ok("Generated: sfdx-project.json")

    # scripts/next_config.template.json
    config_template = {
        "_instructions": "Copy this file to next_config.json and fill in your values. Never commit next_config.json.",
        "sf_login_url": "https://login.salesforce.com",
        "client_id": "<Connected App Consumer Key>",
        "client_secret": "<Connected App Consumer Secret>",
        "refresh_token": "<OAuth Refresh Token>",
        "data_cloud_domain": "<your-dc-domain.c360a.salesforce.com>",
        "ingestion_connector_name": "demo_ingest",
        "connector_sf_id": "",
        "connector_uuid_name": ""
    }
    (project_dir / "scripts" / "next_config.template.json").write_text(
        json.dumps(config_template, indent=2) + "\n"
    )
    ok("Generated: scripts/next_config.template.json")

    # scripts/requirements.txt
    requirements = "requests>=2.31.0\n"
    (project_dir / "scripts" / "requirements.txt").write_text(requirements)
    ok("Generated: scripts/requirements.txt")

    # .gitignore
    gitignore = """# Salesforce cache
.sf/
.sfdx/
.localdevserver/

# Credentials — never commit
scripts/next_config.json
.env

# Dependencies
node_modules/
__pycache__/
.venv/
venv/

# Coverage
coverage/
.eslintcache
"""
    (project_dir / ".gitignore").write_text(gitignore)
    ok("Generated: .gitignore")

    # ── STEP 5: Generate starter prompt ─────────────────────────────────────
    step(5, 5, "Your starter prompt for Claude Code")

    starter_prompt = _build_starter_prompt(demo_name, industry, persona, story, org_alias)
    prompt_path = project_dir / "STARTER_PROMPT.txt"
    prompt_path.write_text(starter_prompt)
    ok(f"Generated: STARTER_PROMPT.txt")

    # ── Print summary ─────────────────────────────────────────────────────────
    banner("Step 3 Complete — Your Demo Project Is Ready")
    print(f"""
  Project created at: {project_dir}

  Files:
    CLAUDE.md                        Context for Claude (pre-filled with your demo)
    sfdx-project.json                Salesforce DX project config
    .mcp.json                        Salesforce DX MCP server
    .claude/settings.local.json      Permission allowances for both MCPs
    scripts/next_config.template.json  Credentials template
    .gitignore                       Excludes secrets and caches
    STARTER_PROMPT.txt               First prompt to give Claude Code

  ─────────────────────────────────────────────────────────

  TO START BUILDING:

    1. Open the project in Claude Code:
         cd {project_dir.name}
         claude

    2. Authenticate the Tableau Next MCP (once per session):
         /mcp

    3. Paste the contents of STARTER_PROMPT.txt to Claude.
       Claude will explore your semantic models and propose
       a dashboard layout for your demo story.

  ─────────────────────────────────────────────────────────

  REMINDER: If you haven't run the first two setup scripts:
    - setup_01_salesforce_mcp.py  — Salesforce DX MCP
    - setup_02_tableau_next_mcp.py — Tableau Next MCP
""")

    print("  Your starter prompt:\n")
    print("  " + "─" * 60)
    for line in starter_prompt.splitlines():
        print(f"  {line}")
    print("  " + "─" * 60)
    print()


def _build_starter_prompt(demo_name, industry, persona, story, org_alias):
    return f"""I'm building a Salesforce + Tableau Next demo for a {industry} customer.

Persona: {persona}
Story: {story}
Org: {org_alias}

Please start by exploring what data is available:
1. List the semantic models in my Tableau Next org
2. For the most relevant model(s), describe the key measures and dimensions
3. Based on the demo story above, propose a dashboard layout with 3-5 components that tell a coherent narrative

For each proposed component, describe:
- What it shows and why it matters to a {persona}
- What SDM metric or dimension drives it
- Whether it should be a native Tableau Next component or a custom LWC

Don't build anything yet — I want to review the proposal first.
"""


if __name__ == "__main__":
    main()
