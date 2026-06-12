# Acceptance Rules

Benchmarks decide whether changes stay.

## Automatic Reject

Reject automatically if:

```text
- engine fails to build
- any perft test fails
- engine crashes during match
- illegal move occurs
- tactical accuracy drops more than 3%
- nodes/sec drops more than 15% without clear Elo gain
```

## Accept Conditions

Accept only if:

```text
- correctness tests pass
- no crashes
- performance does not regress badly
- match result justifies keeping change
```

## Initial Match Rule

Accept if:

```text
- at least +15 estimated Elo over baseline
- at least 200 games played
- tactical accuracy does not drop more than 2%
```

## Future Improvement

Later, replace simple Elo threshold with SPRT-style testing or confidence intervals.

## Links

- [[research-loop]]
- [[data-contracts]]

