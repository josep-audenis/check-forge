# Agent Maintenance

This wiki is an LLM-maintained compiled knowledge base, not a static document.

## Operating Model

Layers:

```text
raw sources -> wiki notes -> schema/maintenance rules
```

Raw sources are source of truth and should not be rewritten during ingest. Wiki notes are synthesized, interlinked, and updated as understanding improves.

## Before Answering Project Questions

Read:

```text
docs/wiki/index.md
```

Then read linked pages relevant to question.

## When Adding Or Changing Sources

On ingest:

```text
1. Read source.
2. Create or update source summary page.
3. Update relevant topic pages.
4. Add cross-links.
5. Update docs/wiki/index.md.
6. Append docs/wiki/log.md.
```

## When Changing Project Code

Update wiki in same change if work affects:

```text
- repository structure
- build/test/benchmark commands
- engine CLI or UCI behavior
- config schema
- benchmark result schema
- experiment workflow
- acceptance/rejection rules
- dashboard data contract
- roadmap status
```

## When Answering Useful Questions

If answer creates durable project knowledge, file it into wiki:

```text
- create new topic page when concept is reusable
- update existing page when answer refines current plan
- update index
- append log entry
```

## Periodic Lint

Check for:

```text
- contradictions between pages
- stale roadmap claims
- orphan pages
- missing cross-links
- source summaries missing from index
- code behavior differing from wiki
- schemas documented but not implemented
```

## Rules

```text
- preserve experiment history
- do not rewrite finalized reports
- prefer links over duplicated long sections
- keep pages short and focused
- append log entries with "## [YYYY-MM-DD] action | title"
- when code and wiki disagree, verify with tests or source files, then update wiki
```

## Links

- [[index]]
- [[log]]

