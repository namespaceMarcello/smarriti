# Smarriti

*Working title. "Smarriti" is Italian for "lost ones".*

An open-source engine that tells you **where to look for a lost pet right now**.

When a cat or a dog goes missing, people post on Facebook, tape flyers to lampposts and
walk around at random. Nobody can say where it makes sense to search next, and nobody
records where animals are eventually found. This project fixes both.

## The idea

A lost animal is in one of two states, and every passing hour makes the second more likely:

| State | What matters | What helps |
|---|---|---|
| **Loose** | it moves: places matter | a map: where to search, where to put flyers |
| **In someone's hands** | picked up, taken to a vet or a shelter | finding that person: shelters, vets, microchip |

The engine is a particle filter: thousands of virtual animals leave home and move by
category rules (an indoor cat hides within a few houses; a fearful dog runs along
streets; a friendly dog walks up to people). Every hour some get picked up. Every real
**sighting** removes the particles that could not have been there; every **search** that
found nothing thins the area by the method's probability of detection. Where the most
particles remain, the map is dark.

Three outputs, not a number:

- *Search here, at this hour.*
- *A flyer is missing here.*
- *From today it pays to call: here are the shelters and vets within N km.*

## How the data arrives

We do not scrape social networks. Every announcement carries a way back to us: the owner
gets a printable flyer and a post text, both with a QR code and a link — *"Seen it? Tap
here"*. Whoever sees the animal taps once and marks **where and when**. Volunteers who
search leave "searched here" tracks. Every flyer has its own QR, so we know which ones
bring sightings.

It is a website opened from a link or a QR code. Nothing to install.

## Method

The movement rules start from published numbers (1,210 lost cats: 75% found within
500 m, median 50 m; Dallas strays: 70% picked up within 1.6 km) and are calibrated on
real cases. Every prediction is written down **before** the measurement, and a negative
result is recorded like any other. The same maths runs behind wilderness search and
rescue and the search for Air France 447; nobody had put it together for pets.

Where a case closes, the find point, the time and the way it was found become data. For
lost people such a database (ISRID) has 150,000 cases; for pets it does not exist yet.

## Status

Design phase, September 2026. No code yet. The documentation is in Italian for now:

- What we build, and what we deliberately do not: `docs/progetto.md`
- The full design of the simulator (states, categories, parameters, evidence, validation
  phases): `docs/simulatore.md`
- The maths: `docs/matematica.md`
- Studies and open datasets, with numbers and sources: `docs/riferimenti.md`
- Decisions, open problems, next steps: `docs/STATO.md`
- Predictions and measurements: `docs/MISURE.md`

## License

AGPL-3.0. Improvements stay in the commons.
