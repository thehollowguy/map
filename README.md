# map

AI tuning playground for Stellaris-style strategy scripting.

## Repository layout

- `strat.ai` – main strategic AI evaluator, action planner, doctrine selector, and ship-design logic.
- `FG.ai` – auxiliary/experimental AI rule set used for comparisons and alternative policy tuning.

## Working with the scripts

The `.ai` files in this repository are Lua-like script files. Useful local checks:

```bash
# Syntax check (if luac is installed)
luac -p strat.ai
luac -p FG.ai
```

```bash
# Alternative syntax check via Lua (if lua is installed)
lua -e "assert(loadfile('strat.ai'))"
lua -e "assert(loadfile('FG.ai'))"
```

## Notes

- Keep balancing changes explicit and easy to diff (tables, coefficients, and rule names).
- Prefer deterministic scoring/action logic for reproducible behavior tuning.
