# Smarriti

*Working title. "Smarriti" is Italian for "lost ones".*

An open-source mathematical simulator that predicts **where a lost pet is right now**.

When a cat or a dog goes missing, nobody can say where it makes sense to search: people
walk around at random. Studies tell how far lost animals go, how soon they are found and
how temperament changes both, but nobody has turned that into a map for a single case.

## The idea

Given the animal, its home, the kind of place it lives in and the time it was lost, the
simulator releases thousands of virtual animals from home and moves them hour by hour with
rules per category: an indoor cat hides within a few houses, a fearful dog runs far, a
friendly dog walks up to people. The surroundings change the rules (apartment blocks,
houses with gardens, city centre, countryside, parks). Every hour some are picked up by
someone. Where the most remain, the map is dark. Nothing is fed in after the loss: only
maths and published data.

A lost animal is in one of two states, and every passing hour makes the second more likely:

| State | What matters | What helps |
|---|---|---|
| **Loose** | it moves: places matter | the map: where to search |
| **In someone's hands** | picked up, taken to a vet or a shelter | finding that person: shelters, vets, microchip |

Outputs: the map (PNG and GeoJSON), the probability of each state, where to search first
and at what hour, the radius holding half and nine tenths of the chance, and whether it is
time to call shelters and vets.

## Try it

```bash
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install numpy scipy matplotlib pytest
.venv/Scripts/python -m sim cases/esempio-gatto.json --now 2026-09-22T08:00 --out out/
.venv/Scripts/python -m pytest -q
```

## Method

The movement rules are calibrated on published numbers (1,210 lost cats: 75% found within
500 m, median 50 m; Dallas strays: 42% picked up within 120 m, 70% within 1.6 km). Every
prediction is written down **before** the measurement, and a negative result is recorded
like any other.

## Status

Simulator v0, September 2026: it runs and is calibrated on the published distances; it
does not yet beat the simpler ring model (`docs/MISURE.md`). The documentation is in
Italian for now: `docs/progetto.md` (what we build), `docs/simulatore.md` (the model),
`docs/matematica.md`, `docs/riferimenti.md` (studies and data), `docs/STATO.md`.

## License

AGPL-3.0. Improvements stay in the commons.
