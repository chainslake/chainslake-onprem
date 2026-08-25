# Chainslake On-Premises

Chainslake is a **Blockchain Data Warehouse** system that ingests on-chain data from EVM-compatible blockchains (Ethereum, BNB, Polygon...) and stores it in a structured data warehouse for analytics and visualization.

The system runs entirely on-premises using Docker, built on open-source Big Data technologies: **HDFS**, **Apache Spark**, **Trino**, **Apache Airflow**, and **Metabase**.

> For detailed architecture and directory structure, see [OVERVIEW.md](./OVERVIEW.md).

---

## Data Agent Team

Chainslake uses an **AI Agent Team** powered by [opencode](https://opencode.ai) to automate data pipeline development and management. Each agent has a specific role and limited workspace permissions.

### Agents

| Agent | Role |
|---|---|
| **@team-lead** | Coordinates the team — receives your requests, assigns tasks, and presents results |
| **@ba** | Business Analyst — gathers your requirements and writes specification documents |
| **@data-architect** | Designs table schemas and writes technical design documents |
| **@data-engineer** | Develops pipeline jobs (.sh/.sql/ABI), deploys to production, manages Airflow DAGs |
| **@tester** | Writes and runs test cases to validate data quality |
| **@data-analyst** | Builds dashboards and visualizations on Metabase |
| **@build** | Develops new scripts, skills, and tools for the team |
| **@plan** | Analyzes requirements and proposes solutions (read-only) |

### Workflow

```
Your request
    │
    ▼
@team-lead ──→ @ba (requirements)
                    │
                    ▼
              @data-architect (design)
                    │
                    ▼
              @data-engineer (develop) ←→ @tester (test)
                    │
                    ▼
              @data-analyst (visualization)
                    │
                    ▼
@team-lead ──→ You (results)
```

> **Fast Path**: For common tasks (add new chain, decode contract, deploy tables), the team-lead can skip the full workflow and assign @data-engineer directly.

---

## Getting Started

### 1. Install opencode

[opencode](https://opencode.ai) is the AI coding platform that runs the agent team.

```bash
# Install opencode (requires Node.js >= 22)
npm install -g opencode

# Or with Homebrew
brew install opencode
```

Verify installation:

```bash
opencode --version
```

### 2. Activate Agents

Navigate to the project directory and start opencode:

```bash
cd chainslake-onprem
opencode
```

On first launch, opencode reads `opencode.json` and loads all agents. The default agent is **@team-lead** — your main point of contact.

Switch agents using the agent selector in the TUI, or simply type your request and @team-lead will coordinate the right agents automatically.

### 3. Start Talking

You don't need to know which agent to call. Just describe what you want in natural language — **@team-lead** will route your request to the right agent(s).

---

## Example Prompts

### Pipeline Management

```
Setup a new chain pipeline for BNB
```

```
Add a decode job for the Uniswap V3 Swap event on Ethereum
```

```
Add a contract info job for USDC on Ethereum
```

```
Deploy the ethereum_decoded tables from dev to production
```

```
Configure the ethereum pipeline to run with 2 partitions per run
```

### Data Analysis

```
Analyze the top 10 most active tokens on Ethereum in the last 7 days
```

```
Create a Metabase dashboard showing daily transaction volume
```

```
Query the total number of blocks processed for each chain
```

### Operations

```
Run the ethereum DAG and verify the data
```

```
Check the status of all pipeline jobs
```

```
Upload this CSV file to the data warehouse
```

### System

```
What scripts are available in the project?
```

```
Build a catalog of all tables in the data warehouse
```

```
Install Chainslake on a new server
```

---

## Contact

The `chainslake.jar` file (main execution file) is not distributed in this repository. To obtain it, please contact the Chainslake Admin.

For issues or support, please create an issue on this repository.
