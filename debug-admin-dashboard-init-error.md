# Debug Session: admin-dashboard-init-error

## Status
[OPEN] Analyzing TDZ error in AdminDashboardScreen

## Session Info
- **Session ID**: admin-dashboard-init-error
- **Date**: 2026-08-21
- **Reporter**: Prod user
- **Symptom**: `Uncaught ReferenceError: Cannot access 'zt' before initialization` at AdminDashboardScreen render
- **Stack**: renderWithHooks → updateFunctionComponent → beginWork (module init phase during hook render)

## Hypotheses
1. **Circular import** between AdminDashboardScreen and a sibling module (e.g., stats widget / chart component / api client) causing a top-level `const`/`let` to be referenced before its declaration by the JS bundler.
2. **Temporal Dead Zone (TDZ) inside component body**: a `const`/`let` declared after a hook call or inline function that references it (minified name `zt`).
3. **Static import of a module that self-references on init** (e.g., barrel `index.ts` re-exporting AdminDashboardScreen while also importing from a file that imports it back).
4. **useMemo/useCallback dependency closure** referencing a variable declared later in the component body, triggered during initial render before that line runs.
5. **Shared state initialization** (store/context) imported in a way that triggers a subscriber that renders AdminDashboardScreen before its module finishes evaluating.

## Evidence Log
| Step | Timestamp | Observation | Verdict |
|------|-----------|-------------|---------|
| 1 | - | Static analysis of imports and top-level declarations | - |
| 2 | - | Runtime instrumentation on module load and component render | - |

## Actions Log
- [ ] Step 1: Static code review of AdminDashboardScreen + related imports
- [ ] Step 2: Add debug instrumentation
- [ ] Step 3: Reproduce & capture evidence
- [ ] Step 4: Apply minimal fix
- [ ] Step 5: Post-fix verification

## Root Cause
_(pending evidence)_
