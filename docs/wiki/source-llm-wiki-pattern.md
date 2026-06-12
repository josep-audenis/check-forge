# Source: llm-wiki.md

Source file:

```text
llm-wiki.md
```

## Summary

This source describes Karpathy-style LLM wiki maintenance: persistent compiled Markdown notes maintained by an LLM, not one-off RAG retrieval.

Core distinction:

```text
Raw sources are read once and integrated into a durable wiki. Future answers use already-synthesized pages, cross-links, contradiction notes, and logs.
```

## Adopted For CheckForge

CheckForge wiki uses:

```text
- index.md as content map
- log.md as append-only timeline
- source summary pages
- short interlinked topic pages
- maintenance rules for future agents
```

## Operations

Adopted operations:

```text
- ingest: read source, summarize, update topic pages, update index, append log
- query: read index first, answer from wiki pages, file durable answers back into wiki
- lint: check contradictions, stale claims, orphan pages, missing cross-links
```

## Source Of Truth

For CheckForge:

```text
- code and benchmark output verify actual behavior
- raw docs preserve original intent
- wiki records current synthesized understanding
```

## Links

- [[agent-maintenance]]
- [[index]]
- [[log]]
