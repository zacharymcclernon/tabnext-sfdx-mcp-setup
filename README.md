# Salesforce + Tableau Next Demo Builder

Three setup scripts that get Claude Code connected to your Salesforce org and Tableau Next analytics — then scaffold a new demo project with full architectural context pre-loaded.

## Run these in order

### Step 1 — Salesforce DX MCP
```bash
python3 setup_01_salesforce_mcp.py
```
- Verifies Node.js, Salesforce CLI, and Claude Code are installed
- Authenticates Claude Code with your Salesforce org
- Writes `.mcp.json` (Salesforce DX MCP server registration)
- Gives Claude access to SOQL, metadata deploy/retrieve, and 80+ org tools

### Step 2 — Tableau Next MCP
```bash
python3 setup_02_tableau_next_mcp.py
```
- Guides you through enabling the Tableau Next MCP server in your org settings
- Guides you through creating an External Client App for OAuth
- Registers the Tableau Next MCP server globally with Claude Code (`claude mcp add`)
- Gives Claude access to `list_semantic_models`, `analyze_data`, `get_semantic_model`, etc.

### Step 3 — New Demo Project
```bash
python3 setup_03_new_demo.py
```
- Asks for your demo context: industry, persona, story, org alias
- Creates a new project directory with all config files pre-filled
- Generates a `CLAUDE.md` with Tableau Next architectural patterns so Claude builds correctly from day one
- Writes a `STARTER_PROMPT.txt` — paste this into Claude Code to kick off your first demo

## What's in the generated project

```
YourDemo/
  CLAUDE.md                      Claude's architectural context (Tableau Next patterns,
                                 API gotchas, SVG visualization approach, deploy order)
  STARTER_PROMPT.txt             First prompt to give Claude — explores your SDMs and
                                 proposes a dashboard layout
  sfdx-project.json              Salesforce DX project config
  .mcp.json                      Salesforce DX MCP server (points at your org)
  .claude/settings.local.json    Permission allowances for both MCP servers
  scripts/
    next_config.template.json    Credentials template (copy → next_config.json, fill in)
    requirements.txt             Python dependencies (requests)
  force-app/main/default/
    lwc/                         Your LWC components go here
    classes/                     Your Apex classes go here
  .gitignore                     Excludes next_config.json and other secrets
```

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- [Salesforce CLI](https://developer.salesforce.com/tools/salesforcecli): `npm install -g @salesforce/cli`
- [Claude Code](https://claude.ai/code): available via VS Code extension, desktop app, or `npm install -g @anthropic-ai/claude-code`
- A Salesforce org with Tableau Next enabled (SDO works well)
- Org admin access (to create External Client App and enable Tableau Next MCP)
