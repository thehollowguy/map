# map

AI tuning playground for Stellaris-style strategy scripting.

## Repository layout

- `strat.ai` – strategic AI evaluator, action planner, meta/counter-meta selector, and adaptive fleet policy logic.
- `FG.ai` – auxiliary/experimental AI rule set used for comparisons and alternative policy tuning.
- `tools/parse_stellaris_save.py` – parser utility that extracts state/meta signals from save data into JSON for `StratAI:tick(...)` input.

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

## Save parsing and meta template seeding

Use the parser to generate state hints (4.0+ ascensions/origins, economy gap, pressure signals):

```bash
python tools/parse_stellaris_save.py /path/to/save.sav --with-steam
```

The JSON output can be merged into your runtime observation payload and consumed by `strat.ai` through fields like:
- `bio_ascension`
- `machine_age_virtuality`
- `shattered_ring_origin`
- `pop_growth_pressure`
- `planet_capacity_pressure`
- `alloy_density`
- `our_total_economy`
- `enemy_total_economy`
- `steam_meta_signals`


## New tuning controls

`strat.ai` now exposes lightweight knobs for behavior shaping without cheats:
- `aggression_slider` (`0.5` to `2.0`) for StarTech-like caution ↔ StarNet-like pressure.
- `difficulty_profile` (`eco_bias`, `tech_bias`, `mil_bias`, `curiosity_enabled`).
- `compatibility` opt-ins for `disable_xeno_compat_opt_in` and `disable_eternal_vigilance_opt_in`.
- `performance.max_projection_months_low_diff` for lower-difficulty simulation capping.

## Notes

- Keep balancing changes explicit and easy to diff (tables, coefficients, and rule names).
- Prefer deterministic scoring/action logic for reproducible behavior tuning.
- The AI now logs rolling `last_eval.components` snapshots each `tick()` via `state.last_eval_components`.
