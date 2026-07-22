# AppWorld test_normal-68 system-design-v2 repair

This is a versioned, source-only repair of the 68 gpt-5.4/high drafts.  It does
not overwrite the earlier v6 packets, remote drafts, or claim freeze.

## Frozen scope

- 68 `test_normal` cases
- 469 released registered tests
- native artifact/visibility and explicit S/F/U aggregation repaired in 68/68
- stronger registry: 34 gap cases, 34 no-gap cases,
  44 conditions
- stronger content actions: 27 cases

## Why packets changed

The old packets embedded `official TestTracker results` in `required_native` as
decisive evidence and embedded the superseded stronger registry.  Because a
draft is an exact projection of those packet registries, changing only YAML/JSON
would be invalid.  Each new packet therefore carries the new visibility contract,
released-evaluator semantic binding, native registry, stronger registry entry,
and the unchanged official 19-file source material.

## Boundary

The complete benchmark record and released label remain preserved outside the
scorer view.  A conforming scorer must use only allowlisted non-verdict evidence
and lock native S/F/U first.  Label comparison and any source-pointer-based
conflict review happen afterwards.  Stronger results remain separate.

## Integration status

This bundle repairs and freezes the case packets and drafts; it does not patch the
reference scoring runner.  That runner currently copies an evidence directory
without enforcing this allowlist, so these assets must not be called end-to-end
label-independent until the scorer-view projection and isolation gate are
implemented and validated.
