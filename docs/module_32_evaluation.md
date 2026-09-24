# Module 32 — Evaluation System Documentation

## Architecture & Design Principles

Module 32 provides an independent observation and measurement framework for MAX.

### Core Domain Entities
- `EvaluationTarget`: Specifies evaluated target entity type (`AI_RUNTIME`, `AGENT_RUN`, `TOOL_INVOCATION`, `PROACTIVE_DECISION`, `PERSONALIZATION_BEHAVIOR`, etc.).
- `EvaluationCase`: Individual test scenario containing prompt input, expected output, reference facts, expected tools, expected security actions, and constraints.
- `EvaluationDataset`: Versioned collection of evaluation cases (including versioned golden datasets).
- `EvaluationRun`: Execution instance tracking case evaluations, metrics, pass rates, and artifacts.
- `EvaluationScore`: Metric score assigned by an evaluator with explicit scale and confidence rating.
- `EvaluationComparison` & `RegressionFinding`: Comparative analysis comparing candidate vs baseline runs to detect metric regressions.
- `EvaluationReport`: Structured report with executive summary, metric breakdowns, failure classifications, subsystem coverage, and informational recommendations.

### Safety & Privacy Boundaries
- **No Autonomous Self-Mutation**: Evaluation findings and recommendations are strictly informational.
- **Redaction & Privacy**: Automatically redacts credentials and API secrets in outputs when `redaction_enabled` is active.
- **Evaluation Isolation**: Evaluator failures do not crash the host system or stop remaining evaluation cases.
