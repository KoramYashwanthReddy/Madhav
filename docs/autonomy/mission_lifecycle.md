# Mission Execution & Replanning Lifecycle

## Lifecycle Sequence
1. **Understand & Decompose**: Goal $\rightarrow$ Objective $\rightarrow$ Milestones $\rightarrow$ Planned Actions.
2. **Pre-flight Safety Check**: Verifies scope boundaries, token/tool budgets, kill-switch state, and authorization rules.
3. **Execution Loop**: Invocations execute strictly via Module 14 Tool Registry and module interfaces (never unmanaged shell/OS calls).
4. **Observation & Empirical Verification**: Output is empirically verified (e.g. file existence) rather than trusting tool return codes.
5. **Replanning & Self-Healing**: On transient failure, requests Module 11 Reasoning replan up to configured max replan limits.
6. **Checkpoint & Recovery**: Persists durable checkpoints with Module 39. Crashed missions recover safely into `PAUSED` state.
