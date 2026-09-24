# Module 31 — Learning & Personalization Engine Documentation

## System Architecture

Module 31 provides behavioral personalization and controlled learning for MAX.

### Core Domain Entities
- `Preference`: Core preference model containing value, source, status, confidence, strength, scope, time window, and context conditions.
- `PreferenceEvidence`: Traceable evidence linking signals and observations to preferences or hypotheses.
- `LearningSignal`: Normalized incoming signal observed across conversation, tasks, notifications, and tool usage.
- `LearningObservation`: Behavioral pattern extracted from one or more signals.
- `PreferenceHypothesis`: Candidate inferred preference evaluated before promotion.
- `PersonalizationProfile`: Aggregated user profile containing Communication, Notification, Proactivity, Autonomy, and Workflow sub-profiles.
- `ResolvedPreference`: Deterministic preference resolution result containing value, source, confidence, scope, and reason.

### Key Workflows
1. **Signal Processing & Hypothesis Lifecycle**:
   `Signal -> Pattern Detector -> Observation -> Hypothesis Engine -> Policy Validator -> Confidence Evaluator -> Promotion -> Preference`
2. **Deterministic Resolution**:
   `PreferenceResolver.resolve(context, category, key)` evaluates active preferences using strict precedence rules.
3. **Decay & Reinforcement**:
   `PreferenceDecayService` applies daily decay to inferred preferences, archiving low-confidence items while preserving explicit preferences.
4. **Data Privacy & Reset**:
   Supports category disabling, resetting inferred preferences, category resets, and learning mode toggling.
