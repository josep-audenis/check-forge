# Dashboard Strategy

UI is useful, but only after benchmark data exists.

## Decision

Do not build dashboard before first real benchmark loop. Build engine and result schemas first.

Best final flow:

```text
C++ engine -> Python benchmarks -> JSON results -> dashboard
```

## Options

Streamlit:

```text
- fastest to build
- good for local research view
- minimal frontend complexity
```

React:

```text
- better portfolio/product feel
- more setup and state management
- worth it after JSON result schema stabilizes
```

Recommended path:

```text
1. Store stable result JSON.
2. Add simple read-only dashboard once experiments exist.
3. Use Streamlit for speed or React for polish.
4. Keep dashboard read-only first.
```

## Initial UI Scope

Show:

```text
- experiment list
- accepted/rejected status
- Elo over time
- tactical accuracy over time
- nodes/sec over time
- perft pass/fail
- links to experiment reports
- baseline vs experiment comparison
```

## Avoid Early

Avoid:

```text
- auth
- database
- live engine board
- complex state architecture
- editing experiments from UI
- dashboard before benchmark data exists
```

## Links

- [[data-contracts]]
- [[implementation-roadmap]]

