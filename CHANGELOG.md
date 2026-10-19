# Changelog

Changes to the model only: physics, accounting, data corrections and enumeration rules, oldest first.  Output formatting and documentation changes are listed only where they changed a published number or its label.  Prices carry the date they were read.  Dollar figures are five-year dollars per average delivered cfm in the average-air scenario unless stated otherwise.

## v1 (legacy design-space simulation, 2026-09-07)

- Enumerated 18 fans (17 Cybenetics measured per-step curves plus a Noctua NF-P12 redux estimated from its spec sheet), 5 fan counts, 13 filter options, 3 filter counts and 10 speed steps, about 35,000 builds.
- Noise on the Cybenetics chamber dBA scale, relative only.  The estimated NF-P12 redux carried a +8.7 dB offset to approximate the Cybenetics bench (Noctua 22.6 dB(A) against Cybenetics 31.3 on the NF-A12x25) and its rows were marked EST.
- MERV 13 single-pass smoke-class catch 0.60, taken from a Tex-Air single-pass bench test at duct velocity and applied unchanged at box velocity.
- Build factor 0.85 for leakage, guards and fan-to-fan interaction, matching FilterBoxBuilder's published model.
- Electricity at $0.1668 per kWh, 24 hours a day.
- Filter life as two alternative models: A, time-driven (8.6 / 3.0 / 2.0 months to 70% of new CADR by scenario), and B, mass-driven (end of life at 0.4 g deposited per sq ft of media).  Both ended life at 70% of new CADR.
- Media area multipliers first assumed at 2x per inch of depth, then corrected to about 2.1x (2 inch) and 2.9x (4 inch) from AAF PREpleat and Koch Green13 datasheets.
- Scenario indoor PM2.5 loads of 8 / 30 / 45 ug/m3 for average, poor and smoke-month air.
- Result at the time: at every noise cap, six to eight 140 mm Arctic fans at 30 to 60% on two 20x25x2 filters, $100 to 130 to build, $1.9 to 2.5 per cfm.  Under model A one 1 inch filter won and the DIY box beat new appliances; under model B two 2 inch filters won and a refurbished Winix on generic filters beat every DIY box.

## v2 (rebuild, 2026-09-07)

- Rebuilt as one tool: every input in `params.json`, fan curves and prices in `fans_data.py`, physics and accounting in `model.py`, and `run.py` writing the workbook and report.
- Filter media types MERV 13, MERV 11, MERV 16 and H11 panel, each with a single-pass catch when new, decay parameters and a resistance model.
- Filter pressure drop from the FilterBoxBuilder MERV 13 polynomial, dp = 4.73e-7 v^2 + 3.38e-4 v (inches of water, v in fpm), other electret grades as multiples of it; H11 panels linear at 56 Pa per 100 fpm.
- Operating point: a straight-line fan curve from free-air cfm to maximum static pressure at each Cybenetics speed step, crossed with the filter curve.  CADR new = airflow x build factor x catch.
- Continuous electret decay replaced the A/B fork: catch(t) = floor + (new - floor) x exp(-t/tau), with tau scaling as (media per cfm / reference)^0.5, and the swap interval optimised for five-year dollars per average delivered cfm.  Mechanical media capped at a 12-month swap.
- One noise scale: per-fan Cybenetics dBA + 10 log(fans) + 2 dB bench-to-3 ft offset, anchored on one measurement (HouseFresh's 41.8 dB at 3 ft on the six-fan Nukit Tempest; 31.9 + 10 log 6 = 39.7).
- Rooms: units stacked to 5 air changes an hour per room, with noise adding 10 log(units).
- Appliances from HouseFresh per-speed readings at the fastest speed under 45 dB at 3 ft, quiet-speed CADR as a clear-time fraction of the AHAM rating where no sub-45 dB CADR was published.
- MERV 16 modeled at catch 0.85 with no fade and 2x the MERV 13 resistance; MERV 11 at catch 0.35 with resistance about equal to MERV 13.
- Efficienado Reference Box (three NF-P12 redux plus one NF-A14 on four 16x25x1) added as a fixed four-fan, four-filter entry with noise measured at 3 ft on 2026-09-07: 44.6 dB at full dial, 33.1 at half dial, 25.4 at the lowest dial, room floor 24.0, anchored to HouseFresh's Winix C545 readings (offset 89.1 dB, plus or minus 1.5).
- About 90,000 builds per run.  Headline: under 40 dB, six Arctic P14 Pro at 60% on one 20x25x1 MERV 16, $2.11; best MERV 13 $2.50.

## v3 (2026-09-07, first review pass)

- Kits now run through the DIY physics (kit price plus first filter set plus power supply) instead of appliance-style rows with no filter decay.
- Removed the double billing of the first filter set.  Convention since: the first set is inside the purchase price, later sets are billed, and appliances follow the same rule (four later yearly sets in five years).
- Decay reference corrected from 0.10 sq ft per cfm (true media area, which the code does not use) to 0.047 in the model's own media units (four 20x20x2 at about 500 cfm: 4 x 2.78 x 2.14 = 23.8 units).
- Scenario loads 8 / 30 / 45 -> 8 / 20 / 28 ug/m3; the 45 exceeded every with-cleaner value in its source.
- Electricity rate 0.1668 -> 0.1635 $/kWh (the earlier formula left the basic charge's share of fees in the numerator).
- Media multipliers set to 2.14 (2 inch) and 2.97 (4 inch), datasheet means of AAF and Koch.
- MERV 11 catch 0.35 -> 0.27 with resistance 0.73x MERV 13.  MERV 16 resistance 2x -> 1.3x, modeled as electret with the MERV 13 decay, swap cap removed.
- Winix 5500-2 (discontinued May 2025) replaced by Winix 5510 and refurbished C545 rows; Blue Pure 211+ moved to speed 1 (37.2 dB, 16.9 W); Tempest kit priced without the power supply; Tempest Pro added; Coway filter set $54.99, Winix OEM Filter H $84.99, box-fan CR box filters $60.32 a year.
- Arctic fan prices moved to buyable singles.  Cybenetics chamber-floor steps (6.0 dBA) excluded from the enumeration.  Estimated-fan (EST) rows excluded from the best-DIY selection.
- Reference Box half dial placed at 59% of full rpm from the measured 11.5 dB drop (50 log law).
- 87,111 builds.  Headline: under 45 dB, 8 x Arctic P14 PWM PST at 100% on four 20x25x1 MERV 16, $1.90, against the refurbished C545 on generic filters at $1.98; Reference Box at full dial $2.26.

## v4 (2026-09-07, second review pass)

Validation: the model was run against seven measured PC-fan boxes (Nukit Tempest, CleanAirKits Luggable XL-7, XL Ultra, 5-Arctic and 5-SickleFlow, the Tex-Air six-fan cube, AirFanta 3Pro) from HouseFresh PM1, AHAM-verified smoke, CleanAirKits' Intertek and salt-aerosol chamber tests, Tex-Air, and an independent third-party Tempest reading.  At catch 0.60 the model predicted 0.63 to 0.71 of measured CADR while airflow tracked within plus or minus 6% (implied build x catch 0.72 to 0.81, mean 0.77), so the catch was the wrong scalar.  At 0.85 x 0.85 the fit is 0.94 of measured (range 0.89 to 1.01).

- MERV 13 catch 0.60 -> 0.85 (range 0.78 to 0.90).  Electret and diffusion capture both rise as face velocity falls, and these boxes run 33 to 70 fpm.  Tempest modeled CADR 161 -> 228.
- MERV 11 catch 0.27 -> 0.77, from CleanAirKits' paired MPR 1900 vs MPR 1085 chamber tests (MERV 11 at 0.95 to 1.05 of MERV 13 CADR in three boxes).
- MERV 16 catch 0.85 -> 0.90.  H11 panel resistance 56 -> 28 Pa per 100 fpm (56 implied 41 to 57% fan efficiency at AirFanta's measured 213 cfm on 9 W).
- Build factor for sealed kits 0.85 -> 0.90; DIY stays 0.85.
- HEPA appliance loading modeled: average CADR = new x 0.97 / 0.90 / 0.85 by scenario, from Huang 2024's loaded-filter CADR curve on a Winix C535.
- Winix C545 refurbished rows: 9.1 W (a 5500-2 proxy) -> 10.15 W (HouseFresh speed 3); generic filters $17 -> $24 a year to cover carbon at the 3-month cadence.  Generic $/cfm 1.98 -> 2.04 at the watt fix.
- Winix 5510 row rebuilt from HouseFresh's 5510 review: $200, Filter Q $79.99 (not Filter H), speed 2 at 40.8 dB and 6.58 W, sub-45 dB CADR 125 cfm (was a 5500-2 proxy at 42.5 dB, 9.1 W, 118 cfm, $259.99).
- Blue Pure quiet CADR 156 -> 140 (HouseFresh's own speed-1 figure), priced at the 211i Max successor; IQAir filters $200 -> $203 a year; a new C545 row at $129.99 added.
- Appliance "filters per year" put on the same annualised basis as DIY rows (later sets / 5); the swap cap that was silently tied to the five-year horizon set to none; kit rows guarded against zero CADR; Reference Box confined to its own filters and excluded from best-DIY and room winners (its fan price includes a free spare).
- Swap-cap sensitivity (24 and 36 months) added to the report: forcing a swap inside 24 months costs 9 to 17% in average air.
- 106,758 builds.  Headline: under 45 dB, 8 x P14 PWM PST at 100% on four 20x25x2 MERV 13, $184, $1.50; under 40 dB, 6 x P14 PWM PST at 90% on four 20x25x2 MERV 13, $158, $1.61.  MERV 16 no longer leads at any cap.  Reference Box at full dial $1.38 on Nordic Pure MERV 13, $1.60 on Filtrete 1900.  Best appliance AirFanta 3Pro $2.21; refurbished C545 on generic filters $2.35.

## v5 (2026-09-07, third review pass)

- MERV 11 resistance 0.73x -> 0.95x MERV 13 (Tex-Air bench: Filtrete 1085 0.20 vs Filtrete 1900 0.21 inches of water at 300 fpm; the 0.73 traced to a mis-transcribed row).  MERV 11 catch 0.77 -> 0.85, re-solved per box with the corrected resistance (0.80 to 0.88, mean 0.85).  The winning media flips to MERV 11 at every cap, by 3 to 4%; the flip threshold is catch 0.80.
- MERV 16 catch 0.90 -> 0.96 (Nordic Pure's published 96% at 0.3 to 1 um; the ASHRAE 52.2 E1 floor for the grade is 95%).
- Reference Box half-dial anchor moved from the 60% step to the 51% step: the 11.5 dB drop is 0.589 of full rpm by the 50 log law, and on the Noctua map (550 rpm at 20%, 1,700 at 100%) that is 51% PWM, not 60%.  CADR at the measured 33.1 dB falls about 14%; that row 1.77 -> 1.96.  Only the 51% and 100% steps are labeled measured; other steps say fan law.  The measured levels are now read from `params.json`.
- Five-year average catch now credits the partial last swap cycle (at a 36-month interval, 1.613 -> 1.545 on the headline build); the sawtooth that pinned every optimum to a divisor of 60 is gone.
- Winix C545 new ships with two years of filters: 3 later sets, not 4 (3.87 -> 3.34 before the derate change below).
- Appliance loading derate 0.97 / 0.90 / 0.85 -> 0.95 flat: Huang's 7.2-month loading figure is at Turbo, and the quiet speeds modeled here push about 2.3x less air.
- Box-fan CR box moved off the HEPA derate onto the electret decay its MERV 13 media actually follows (four 20x20x1, 274 cfm, 12-month swap): 3.44 -> 4.40 average, 3.93 -> 6.15 smoke month.
- Coway 8.7 -> 9.0 W (ionizer on, matching its CADR); Blue Pure priced at list $349.99 instead of a $262.49 sale; IQAir filters $203 -> $151.32 a year at the manufacturer's current prices, on its stated 10 h/day basis.
- Nukit Tempest Pro split into two rows: the Arctic P14 upgrade with the fans priced (+$77.94) and a stock-fan row on the vendor's lab figure (222 cfm at 37 dBA).  Four stock and availability notes corrected.
- Arctic P12 PWM PST $10.39 -> $16.08; Arctic P12 Pro 10% step 6 -> 1.9 dBA (still excluded as below the chamber floor); be quiet! SW4 140 high-speed $24.50; fan footprint computed from the fan's size (was 120 mm else 140 mm).
- Kept, with flip points stated: tau 10.8 months (the two anchors bracket it at 3.2 to 16 once put on the same clock and particle band), decay floor 0.42 (the no-swap result flips below 0.376, and the two cited floor anchors, 0.407 and 0.375, straddle that), 2 inch vs 1 inch within 1%.
- 107,148 builds.  Headline: under 45 dB, 8 x P14 PWM PST at 100% on four 20x25x1 MERV 11, $161, $1.46 (MERV 13 $1.50); under 40 dB, 6 x P14 PWM PST at 90% on four 20x25x1 MERV 11, $135, $1.56.  Reference Box $1.38 at full dial, $1.96 at half dial.  AirFanta $2.26; refurbished C545 generic $2.40; new C545 $3.41.

## v6 (2026-09-07, fourth review pass, diff check of v5)

- Rooms and swap-curve tables had lost the Reference Box's measured half-dial rows when the step moved from 50 to 51; they now read the measured steps (51, 100) from the fan record.
- Fan price policy stated and applied uniformly as MSRP (P12 PWM PST $11.99, P14 PWM PST $12.99, P14 Max $15.99, P14 Pro PST $16.33, P12 Pro $16.49); marketplace listings excluded.  The P14 PWM PST's $12.99 "in stock" evidence was itself a marketplace listing, so that fan is priced at MSRP.  An in-stock-only rule would move the 30 dB winner by a cent.
- MERV 11 catch restored to the stated assumptions: at the low end of its own 0.80 to 0.88 range MERV 13 wins every cap, so MERV 11 vs MERV 13 is a tie inside the error.
- Winix C545 new counts the two shipped sets in its sets column; Blue Pure reports its 6-month part; H11 panel rows stated as pessimistic (floor 1.0 with a 12-month cap credits no CADR for the swaps it pays for); the NF-P12 EST +8.7 dB offset noted as including about 1.4 dB of a 2,134 vs 2,000 rpm speed difference.
- Headline unchanged.

## v7 (2026-09-07 to 08, pack pricing)

- All 61 price rows (fans, filters, appliances, kits) reread in a browser on 2026-09-07 at Amazon, Micro Center, Lowe's, Walmart, Target, Newegg and the manufacturer stores, first-party or Amazon-sold and in stock, at the pack sizes a builder would buy.
- Pack-based pricing: the cost of N fans or k filters is the cheapest combination of packs that covers the build, spares paid for, applied to the first filter set and to every later set (`fan_packs`, `filter_packs`).  The MSRP rule is retired.
- Fan packs read: P14 PWM PST $12.99 single or $48.99 for 5; P14 Max $10.99; P12 PWM PST $11.99 or $28.99 for 5; P14 Pro PST $7.49 single; P12 Pro $6.39.
- Appliance and kit inputs from the same read: C545 new $159.99; generic Filter S $25.99; Winix 5510 $180; a generic Filter Q row at $27; Coway filter set $22; Dyson generic filter $28; power supply $7; box-fan CR box $59.37 to build (Lasko $23.37 plus an Aerostar 4-pack $35.99).  The base Tempest kit retired (no live listing); Tempest Pro with the P14 upgrade $447.93 plus filters.
- Headline moved to 8 x Arctic P14 Pro PST on four 20x25x2 MERV 11 at every cap ($1.33 to $1.36); without the Pro fans, 8 x P14 Max on the same filters ($1.35 to $1.61).

## v8 (2026-09-08, price corrections and two source reads)

- Corrections after a second look at the read: P14 Pro PST 5-pack $18.09 -> $22.29; Filtrete 1900 $15.00 each; generic Filter S $27.99 for 4 HEPA and 4 carbon (one set a year); generic Filter Q $26 for two yearly sets ($13 a year); Coway $22 stands.
- Huang and Boor 2026 read in full: the MERV 13 electret E1 fall from 72% to 27% is confirmed (relative floor 0.375 at one year, 0.32 at the minimum, recovering to 0.46 at two years), implying tau 5 to 8 months on these boxes.  tau 10.8 and floor 0.42 kept, with the flip stated.
- Nordic Pure MERV Data Product Guide 2025 Q4 read in full: MERV 13 at 0.26 inches of water at 300 fpm confirmed, electret confirmed, E1 50 to 75% for the standard line.  The guide has no MERV 16 row, so the earlier "0.33 at 295 fpm" was a misread and the 1.3x MERV 16 resistance is an assumption (the headline is insensitive to it).
- Reference Box: $1.50 as bought (January sale price plus a free spare fan, spec-sheet airflow), $1.71 at the current fan price, about $1.90 with a 10% spec-to-bench airflow derate.
- Headline: under 40 dB, 8 x P14 Pro PST at 50% on four 20x25x2 MERV 11, $120, $1.38, 33.0 dB; under 45 dB, 8 x P14 Max at 60% on the same filters, $164, $1.35.  AirFanta $2.26; 5510 on generic Filter Q $2.35; refurbished C545 generic $2.54.

## v9 (2026-09-08, wiring constraint)

- Controller modeled as it is sold: four outputs and a 24 W power brick.  Arctic PST fans daisy-chain at no cost; other fans beyond four add a splitter ($7 for up to six fans, $9 for up to eight).
- Builds whose fans would draw more than the brick's rating at the chosen speed are dropped from the enumeration (1,248 per scenario).
- Noise column relabeled to state its construction (per-fan bench dBA + 10 log N + 2 dB).
- Comparison: four P14 PWM PST on the Reference Box's own filters come to $1.70 at 39.9 dB.
- Headline unchanged: 8 x P14 Pro PST at 50% on four 20x25x2 MERV 11, $120, $1.38, 33 dB.

## v10 (2026-09-16 to 17, fifth review pass: physics and modeling)

- Filter pressure drop now depends on pleat depth: `dp_area_factor_by_depth` {1: 1.0, 2: 1.76, 4: 1.76}.  The 2 inch factor is fitted to FilterBoxBuilder's published readings with 8 x Arctic P14 PWM PST (20x20x1 340, 20x20x2 372, 20x25x1 354 cfm).  4 inch equal to 2 inch is an assumption (Nordic Pure rates them equal at 500 fpm).
- Nukit Tempest Pro stock row: the first filter set was missing and filters were priced at $21.66 instead of the $32.39 pack.  Now five sets at $32.39; 3.43 -> 3.91.
- Blueair Blue Pure 211+: eight later filters were billed where nine are needed on the 6-month cadence.  Now $69.99 x 9; 7.75 -> 8.28.
- IQAir: later filters billed as the discrete replacement parts, $639.97, through `appliance_options.later_filters_usd`; 26.24 -> 26.67.
- `fan_packs` keys for the Phanteks T30 and Arctic P12 Max Black did not match their `fans_data` names.  Renamed to match.
- Noctua NF-P12 redux maximum power corrected to 1.08 W.  The Reference Box's fourth fan is the NF-A14 FLX (datasheet 1,200 rpm, 68.0 cfm, 1.51 mm H2O, 19.2 dB(A), 0.96 W); rows had used the PWM variant's 82.5 cfm, 2.08 mm H2O and 1.56 W.
- The Reference Box controller is a 3 to 12 V voltage dial, not PWM.  Reference Box and estimated-fan steps are now percent of full speed; the PWM-to-rpm map is removed.
- Half dial located from floor-corrected levels (24.0 dB room floor): 57% of full speed, fan-only 32.5 dB.
- Decay reference `media_per_cfm_ref_sqft` set to 0.0476 (was rounded to 0.047).
- The note comparing the MERV 13 polynomial with datasheet resistance corrected; the absolute pressure drop at box velocity is uncertain by about 2x.
- `controller_max_watts` 24 -> 36: the power brick is rated 3 A at 12 V; the 24 W figure belonged to a two-output sibling product.  106,206 builds enumerated; the headline result is unchanged by this fix.
- Headline: strict winner 8 x Arctic P14 Pro PST at 50% on two 20x25x2 MERV 11, 285 cfm, 33.0 dB, $93, $1.29, one swap at 30 months.  The four-filter cube on the same fans and media: 303 cfm, $120, $1.32, no swap.  Poor air $1.48, smoke month $1.51 on the two-filter build.  Appliance and kit ranking unchanged.

Validation: against the same seven measured boxes the v10 model predicts 0.89 to 1.05 of measured CADR, mean about 0.97.
