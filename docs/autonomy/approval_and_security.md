# Human-in-the-Loop Approvals & Security Controls

## Core Security Boundaries
- **AI Output is Untrusted**: AI model reasoning cannot self-approve requests or grant security permissions.
- **Prompt Injection Defense**: External inputs (webpages, documents, GitHub issues) are parsed strictly as passive DATA and cannot modify policy, change permissions, or trigger tool calls.
- **Approval Expiration**: Approval requests have explicit timeouts (`expires_at`). Expired approvals cannot authorize future actions.
- **Global Emergency Kill Switch**: Immediately halts all active/queued autonomous missions.
