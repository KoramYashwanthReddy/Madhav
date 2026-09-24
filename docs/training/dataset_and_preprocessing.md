# Dataset Architecture, Preprocessing & Data Security

## Dataset Format Support
Module 40 supports instruction and conversational datasets in JSONL, JSON, and CSV formats.

### Instruction Format
```json
{
  "instruction": "Summarize user preferences.",
  "input_text": "User prefers detailed technical explanations.",
  "output_text": "The user prefers high-depth technical responses.",
  "metadata": {"source": "authorized_export"}
}
```

### Conversational Format
```json
{
  "messages": [
    {"role": "system", "content": "You are MAX personal assistant."},
    {"role": "user", "content": "Hello MAX."},
    {"role": "assistant", "content": "Hello! How can I assist you today?"}
  ]
}
```

## Data Poisoning & Prompt Injection Protection
Training datasets are strictly treated as **passive data payloads**. Dataset content cannot:
- Execute system commands or terminal scripts
- Alter Module 15 security permissions
- Grant tool access or change system configuration
- Trigger automatic model deployment

## Dataset Validation & Cleaning
- **Validation**: `DatasetValidationService` checks required fields, malformed samples, and token distribution.
- **Deduplication**: `DataCleaner.deduplicate()` removes exact duplicate instruction-output pairs.
- **Leakage Detection**: `LeakageDetector` checks overlap between training, validation, and test splits.
- **Versioning**: All datasets are checksummed with SHA-256 and assigned version strings (`v1`, `v2`).
