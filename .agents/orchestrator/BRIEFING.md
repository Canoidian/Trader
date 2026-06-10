# BRIEFING — 2026-06-08T13:50:00Z

## Mission
Build a live-trading crypto bot for Kraken that executes small trades with fee awareness and lightweight self-learning capabilities.

## 🔒 My Identity
- Archetype: orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /Users/williamisaak/Projects/KrakenTraderV2/.agents/orchestrator
- Original parent: 62c4f8f0-a6c2-4745-9fd8-73aa83eca627
- Original parent conversation ID: 62c4f8f0-a6c2-4745-9fd8-73aa83eca627

## 🔒 My Workflow
- **Pattern**: Project / Canonical
- **Scope document**: /Users/williamisaak/Projects/KrakenTraderV2/PROJECT.md
1. **Decompose**: Split into API/Execution, Backtesting, and Research/Analysis modules.
2. **Dispatch & Execute**:
   - Delegate (sub-orchestrator): Spawn a sub-orchestrator for the milestones.
3. **On failure**: Retry, Replace, Skip, Redistribute, Degrade
4. **Succession**: At 16 spawns, write handoff.md, spawn successor.
- **Work items**:
  1. Kraken API integration & execution logic [IN_PROGRESS]
  2. Backtesting & Fee verification script [IN_PROGRESS]
  3. Lightweight analysis & coin ranking script [IN_PROGRESS]
- **Current phase**: 2
- **Current focus**: Monitoring replacement sub-orchestrators for M1, M2, and E2E Tests.

## 🔒 Key Constraints
- Must subtract Kraken trading fees in backtesting.
- Analysis must run completely locally, low memory/GPU usage.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh

## Current Parent
- Conversation ID: 62c4f8f0-a6c2-4745-9fd8-73aa83eca627
- Updated: 2026-06-08

## Key Decisions Made
- Decomposing the project into API integration, Backtesting, and Analysis modules.
- Replaced hung sub-orchestrators due to timeout > 20 mins.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| M1 Orch | self | API & Backtest Core | in-progress | d0f219a7-c31e-4b5e-976a-c46110f9035d |
| M2 Orch | self | Analysis Engine | in-progress | 988a1b68-a4fc-43b0-8a75-2306310ca2f7 |
| E2E Orch| self | E2E Tests & TEST_READY | done | 63d414da-ac51-4570-93a4-5fa79405a979 |

## Succession Status
- Succession required: no
- Spawn count: 9 / 16
- Pending subagents: 
  - d0f219a7-c31e-4b5e-976a-c46110f9035d
  - 988a1b68-a4fc-43b0-8a75-2306310ca2f7
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: 4fbf9e82-fdc6-4bac-9c76-c7a5fb57b13f/task-30
- Safety timer: none

## Artifact Index
- PROJECT.md — Global architecture and milestones
- .agents/orchestrator/progress.md — Execution tracking
- .agents/orchestrator/plan.md — Specific tasks
