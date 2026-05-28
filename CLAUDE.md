# CLAUDE.md — {{DEMO_NAME}}

## Demo Overview

**Industry**: {{INDUSTRY}}
**Persona**: {{PERSONA}}
**Story**: {{STORY}}
**Org alias**: {{ORG_ALIAS}}

---

## Architectural Rules

### Tableau Next Only — No Tableau Cloud

- **NEVER** create Tableau Cloud embeds, iframes, or CRM Analytics dashboard references.
- **ALL** analytics are built using Tableau Next semantic models, surfaced through LWC components with native SLDS styling.
- Use the Tableau Next MCP tools (`analyze_data`, `get_semantic_model`, `list_semantic_models`) to discover and query data before building any component.
- Every chart or metric must tell a coherent story — no isolated numbers without context.

### LWC-First

- Build all UI in Lightning Web Components. No new Aura components.
- Use SLDS styling hooks and Lightning base components (`lightning-card`, `lightning-datatable`, `lightning-progress-bar`, etc.).
- No JavaScript charting libraries (Chart.js, D3, etc.). Use **inline SVG** in LWC templates for all custom visualizations — computed via JS getters, no external dependencies.

### MCP-First Workflow

Before building any analytics component:
1. `list_semantic_models` — discover what SDMs exist in the org
2. `get_semantic_model` — understand the fields, measures, and dimensions available
3. `analyze_data` — prototype the exact query in natural language
4. Build the LWC using SLDS with data shapes confirmed from step 3

---

## Personas

Target one persona per component:

- **Customer** — Experience Cloud portal: their own journey, usage, action items
- **CSM / AE** — Internal app: signal-to-action, account health, renewal readiness
- **Leader / Executive** — Internal app: portfolio health, pipeline, team metrics

---

## Tableau Next Dashboard REST API

All dashboards are built and managed via the REST API at `/services/data/v67.0/tableau/dashboards`.

### Authentication

Store OAuth credentials in `scripts/next_config.json`. **NEVER commit this file.**
Template at `scripts/next_config.template.json`. Run `scripts/reauth.py` to refresh.

### Critical API Gotchas

1. **POST source objects**: Include only `id` and `name`. Do NOT include `type` or `label` — the API returns those on GET but rejects them on POST.
2. **PATCH is blocked**: Returns ACCESS_DENIED. To modify a dashboard, delete and recreate it using `--delete` flag on the build script.
3. **Filter widgets**: Type `filter` is valid. Accepted params: `isLabelHidden`, `receiveFilterSource`, `viewType`. Field binding CANNOT be done via API — configure in the Tableau Next UI after creation.
4. **Filter field binding in UI can corrupt the dashboard**: Configuring filter fields in the UI has been observed to add a `publishers` field to `receiveFilterSource` that the API cannot deserialize, making the dashboard inaccessible. Fix: delete and recreate via the build script.
5. **Extension widget `receiveFilterSource`**: Silently dropped on POST — extension widgets do not support this parameter.

### Grid System

- 72 columns, 16px row height, 16px cell spacing
- Background: `#F4F6F9`, cards: `#FFFFFF` with `#DDDBDA` border, 8px radius
- Margin: 2 columns on each side → usable width = 68 columns

### Widget Types

| Type | Use | Notes |
|------|-----|-------|
| `text` | Titles, labels | Rich text with `content` array |
| `metric` | KPI tiles from SDM | Needs `sdmApiName`, `sdmId`, metric `source.id` |
| `visualization` | Native Tableau Next charts | Needs viz `source.id` from `list_visualizations` |
| `extension` | Custom LWC components | Needs `fullyQualifiedName` (e.g., `c:myComponent`) and LWC bundle `source.id` |
| `container` | Card wrapper | Provides border/background styling |
| `filter` | Dropdown filter | Field binding must be done in UI |

---

## Tableau Next Extensions SDK — Filtering LWC Extensions

Native filter widgets filter LWC extensions via the **Extensions SDK** injected at runtime via `@api sdk`.

### How It Works

1. Declare `@api sdk` in the LWC — the Tableau Next runtime injects the SDK object
2. Subscribe to filter changes: `sdk.on('filterChange', handler)` — returns an unsubscribe function
3. `sdk.getContext()` returns a snapshot of `dashboardState.filters` — use for initial state
4. A `dashboardFilterMixin` utility handles SDK boilerplate (subscription, field name parsing, filter accumulation, polling fallback)

### Critical Details

- Event name is `filterChange` (camelCase) — NOT `FILTER_CHANGE`, NOT `FilterChanged`. Wrong names throw `TypeError: Cannot read properties of undefined (reading 'push')`.
- Filter object shape: `{"fields": [{"model": "TableName.FieldName"}], "operator": "In", "values": ["value"]}`. Field name is at `f.fields[0].model`, NOT `f.field` or `f.name`.
- `filterChange` fires with **only the filter that changed**, not all active filters — accumulate state across events.
- SDK may not be available on first `connectedCallback` — retry via `renderedCallback`.

### What Does NOT Work

- `@api dashboardState` with `targetConfigs` declaration → never populated
- `receiveFilterSource` on extension widgets → silently dropped on POST
- Any filter event name other than `filterChange` (camelCase)

---

## Inline SVG Pattern for LWC Visualizations

All custom charts use pure inline SVG rendered from JS getters that compute coordinates and paths. No external libraries.

```javascript
// Bar chart bar height getter
get bars() {
    const max = Math.max(...this.data.map(d => d.value));
    return this.data.map((d, i) => ({
        x: i * (this.barWidth + this.gap),
        y: this.chartHeight - (d.value / max) * this.chartHeight,
        height: (d.value / max) * this.chartHeight,
        color: d.value > this.threshold ? '#E74C3C' : '#2E86AB',
        label: d.label,
        value: d.value,
    }));
}
```

SVG arc formula for gauges: `M startX,startY A rx,ry 0 large-arc-flag,sweep-flag endX,endY`
- `sweep-flag=1` for clockwise arcs (standard gauge)
- `sweep-flag=0` for counter-clockwise (upward-opening arcs in SVG coords where y points down)

---

## Apex Guidelines

### When to Write Apex

Only write Apex for things that **must** run on-platform:
- `@InvocableMethod` actions for Agentforce and Flow
- LWC controllers (when LDS/GraphQL wire adapters aren't sufficient)
- Triggers and platform event handlers
- Scheduled/batch jobs

### When to Use Python Instead

Use Python for anything that doesn't need to run inside Salesforce:
- Data generation, loading, exploration
- Ad-hoc SOQL queries and record counts
- Prototyping analytics and exploring data shapes
- One-off scripts and validation

Use `simple-salesforce` or the `sf` CLI for Salesforce API access from Python.

### Apex Code Style

- Bulkify all trigger logic
- Use `@AuraEnabled(cacheable=true)` for read-only wire methods
- All `@AuraEnabled` methods need a corresponding test class with ≥75% coverage
- Run `sf apex run test` before deploying

---

## Deployment

### Order Matters

When deploying LWC that references Apex:
1. Deploy Apex classes first
2. Deploy LWC bundles
3. Deploy flexipages last

Otherwise the deploy fails with "Unable to find Apex action class" or "couldn't retrieve design time component information."

### Commands

```bash
# Full deploy
sf project deploy start --source-dir force-app --target-org {{ORG_ALIAS}}

# Assign permission set after any new field deployment
sf org assign permset --name <PermSetName> --target-org {{ORG_ALIAS}}

# Retrieve org changes back to local
sf project retrieve start --source-dir force-app --target-org {{ORG_ALIAS}}
```

### Flexipage Gotchas

- Template `flexipage:recordHomeTemplateDesktop` is the only reliable record page template.
- Region names: `header`, `main`, `sidebar`. No others.
- Do NOT include `<mode>Replace</mode>` on regions.
- Use `force:detailPanel` for record detail, NOT `force:recordDetail`.

---

## Custom Object / Field Visibility

Custom fields are invisible to API/SOQL until a permission set is assigned. After deploying new objects/fields, always run:

```bash
sf org assign permset --name <PermSetName> --target-org {{ORG_ALIAS}}
```

---

## Project Structure

```
force-app/main/default/
  lwc/               LWC components
  classes/           Apex controllers and services
  objects/           Custom object metadata
  staticresources/   JSON data files (if using static resource data)
  permissionsets/    Permission sets
  flexipages/        Lightning page layouts
  messageChannels/   LMS message channels (if using cross-component comms)

scripts/
  build_<dashboard>.py     Dashboard build scripts (one per dashboard)
  reauth.py                Refresh OAuth tokens
  next_config.json         OAuth credentials — NEVER COMMIT
  next_config.template.json Template for credentials
  requirements.txt         Python dependencies
```

---

## Key IDs

Update these after running your build scripts:

```
Org alias:    {{ORG_ALIAS}}
Workspace:    (set after next_setup)
SDM:          (set after build_sdm.py)

LWC Bundles:
  c:<component>:  (set after deploy + registration)

Dashboards:
  <Dashboard Name>:  (set after build script)
```

---

## Common Workflows

### Build a New Dashboard

1. Ask Claude: *"What semantic models are available in my org?"*
2. Ask Claude: *"Describe the fields in [model name]"*
3. Ask Claude: *"Analyze [metric] by [dimension] for the last [period]"*
4. Claude builds a dashboard build script using the Tableau Next REST API patterns above
5. Run: `python3 scripts/build_<name>.py`
6. If the dashboard needs modification, run: `python3 scripts/build_<name>.py --delete && python3 scripts/build_<name>.py`

### Build a New LWC Analytics Component

1. Prototype the data shape with `analyze_data`
2. Claude scaffolds the LWC with inline SVG visualization
3. Deploy: `sf project deploy start --source-dir force-app/main/default/lwc/<component>`
4. Register the LWC bundle ID in the dashboard build script

### Add Filtering to an LWC Extension

1. Declare `@api sdk` in the component
2. Use the `dashboardFilterMixin` pattern — subscribe in `renderedCallback`, unsubscribe in `disconnectedCallback`
3. Remember: `filterChange` (camelCase), filter field at `f.fields[0].model`, accumulate state across events
