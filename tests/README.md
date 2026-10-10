# Legacy inspector checks

From the repository root, run:

```sh
python -B tests/test_legacy_inspector.py
```

The harness requires `lupa` with its Lua 5.1 runtime. The cloud setup already
installs it under `/workspace/.cloud-tools/forever-achievements/python`; a
normally installed `lupa` package works as well.

The checks cover unloaded and populated native UI, safe challenge and reward
evidence, manual snapshot comparison, named descendant fallback, protected
getter failures, forbidden objects, traversal and output budgets, and absence
of hooks, native mutations, unknown API calls, timers, or transmissions.
The copy-window checks cover Run, Clear, Close, retained keyboard input,
widget reuse, wrapped-text sizing, combat deferral, and TOC registration.
Busy UI fixtures verify that ordinary children cannot starve the requested
Legacy pages or their core samples, reward collections honor entry budgets,
and exhausted object budgets prevent namespace key inspection.

These are isolated diagnostic behavior checks. The fixtures do not validate
Forever's actual API availability, native frame contents, or in-game rendering.
Those require running `/legacyinspect` in the client.
