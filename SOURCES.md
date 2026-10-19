# Sources

Every input in `params.json` and `fans_data.py` names its source inline.  This file collects them by role.  Retail prices carry the date they were read (2026-09-07 or 2026-09-08) and the pack size; they will drift.

## Fan performance

- **Cybenetics** fan database (cybenetics.com): per-PWM-step airflow, static pressure, input power and chamber dBA for the 17 bench-tested fans in `fans_data.py`.  Accessed 2026-09-07.  Steps at the chamber floor (6 dBA) are excluded by the model.
- **Noctua** datasheets (noctua.at): NF-P12 redux-1700 (70.75 cfm, 2.83 mm H2O, 25.1 dB(A), 1.08 W) and NF-A14 FLX (68.0 cfm, 1.51 mm H2O, 19.2 dB(A), 0.96 W), used for the estimated NF-P12 rows and the Efficienado Reference Box.  The Noctua-to-Cybenetics noise offset (8.7 dB) is taken from the NF-A12x25, which both publish.
- **Arctic** product pages: PST (PWM Sharing Technology) daisy-chaining, single and pack MSRPs where retail listings were out of stock.

## Filter resistance, media area and catch

- **Nukit FilterBoxBuilder** (filterboxbuilder.com): the MERV 13 pressure-drop polynomial (dp = 4.73e-7 v^2 + 3.38e-4 v inches of water, v in fpm), the 0.85 build factor, and the published 20x20x1 / 20x20x2 / 20x25x1 airflow readings with eight Arctic P14 PWM PST that fix the pleat-depth factor.
- **Nordic Pure MERV Data Product Guide, 2025 Q4** (nordicpure.com): rated resistance and E1 efficiency bands for the standard pleated MERV 13 line (0.26 in. w.g. at 300 fpm; 0.33 and 0.34 in. w.g. at 500 fpm for 2 inch and 4 inch), electret construction, and the absence of a MERV 16 row.
- **Tex-Air Filters** bench data: Filtrete 1085 (MERV 11) vs Filtrete 1900 (MERV 13) resistance on one rig (0.20 vs 0.21 in. w.g. at 300 fpm); single-pass efficiency at duct velocity; the ten-month 24/7 box decay series; the six-fan PC cube (42 dB at 6 ft); the Blue Heaven ASHRAE 52.2 field test of a used MERV 11.
- **CleanAirKits**: paired MPR 1900 vs MPR 1085 chamber tests in three box configurations (MERV 11 at 95 to 105% of MERV 13 CADR), and the Luggable XL-7, XL Ultra and 5-fan Luggable CADR figures used in validation.
- **AAF PREpleat** and **Koch Green13** datasheets: media area per square foot of face by pleat depth (about 2.14x at 2 inch, 2.97x at 4 inch relative to 1 inch).
- **Camfil Megalam H13** panel data: the starting point for the H11 panel resistance, later halved on a fan-power bound from the AirFanta 3Pro.
- **ASHRAE 52.2**: the E1 (0.3 to 1 um) definition the catch parameter is stated on, and the 95% E1 floor for MERV 16.

## Electret decay and filter life

- **Pistochini et al. 2024**: MERV 13 electret efficiency over 40 weeks at 9 hours a day (62 to 75% of new at 0.35 to 1 um).  One of the two "average" decay anchors.
- **Huang and Boor 2026**, Building and Environment 301, 114596: a MERV 13 electret bag filter over 112 weeks in an outdoor-air duct; E1 falling from 72% to 27% in the first year, relative floor 0.375 at one year, 0.32 at the minimum, recovering to 0.46 at two years as a dust cake formed.  The second decay anchor and the source of the floor's flip point.
- **Rosenthal (January 2026)**: used Corsi-Rosenthal box MERV 13 filters testing at MERV-A 10; the four 20x20x2 reference box at about 500 cfm that defines the model's media-per-cfm reference.
- **Huang et al. 2024**, Indoor Environments 1:100057: loaded-filter CADR series on a Winix C535 (0 to 46 g of A2 dust), the basis of the 0.95 appliance loading derate.  Corroboration for direction and magnitude only: Duill 2023, Shaughnessy 1994, Zuraimi 2017, and Smart Air's Sqair loading data.

## Indoor particle scenarios

- **RIOPA study**: median indoor PM2.5 in nonsmoking homes (14.4 ug/m3), reduced about 40% by one cleaner, giving the "average" scenario of 8 ug/m3.
- **Semple et al. 2015**: median indoor PM2.5 in smoking homes (31 ug/m3), giving the "poor" scenario of 20 ug/m3 with a cleaner running.
- **May, Dixon and Jaffe 2021**: a Seattle home running a MERV 13 box fan through the September 2020 wildfire smoke, giving the "smoke month" scenario of 28 ug/m3.

## Appliances, kits and measured boxes

- **HouseFresh** (housefresh.com) reviews: per-speed dB at 3 ft, watts and PM1 CADR for the Winix 5510 and C545, Coway AP-1512HH, Blue Pure 211+, Dyson TP07, IQAir HealthPro Plus, AirFanta 3Pro, the box-fan Corsi-Rosenthal box and the Nukit Tempest.  The Tempest reading (41.8 dB at 3 ft) is the single anchor for the bench-to-room noise offset.
- **AHAM** verified smoke CADR ratings, used where a quiet-speed CADR had to be scaled from a clear-time ratio.
- **Nukit** (Tempest Pro vendor page): independent-lab CADR of 222 cfm at 37 dBA with stock fans, 248 to 299 cfm with Arctic P14 fans, kit price and contents.
- **AirFanta** (air-fanta.com): 3Pro price and H11 panel filter life.
- **IQAir**, **Winix**, **Coway**, **Blueair**, **Dyson** manufacturer stores: list prices, filter part numbers, stated filter lives and what ships in the box.

## Prices and hardware

- Retail reads on 2026-09-07 and 2026-09-08 at **Amazon**, **Micro Center**, **Lowe's**, **Walmart**, **Target**, **Newegg** and the manufacturer stores, first-party or Amazon-sold, in stock on the read date, at the pack sizes a builder would buy.  Marketplace listings are excluded.  Every read is recorded with its store in `fan_packs`, `filter_packs`, `filters` and `appliances`.
- **Delinx** 3 to 12 V variable-voltage fan controller listing: four outputs, 3 A at 12 V (36 W), used for the controller cost, output count and power cap.
- The electricity rate (0.1635 $/kWh) is the marginal residential rate reconstructed from a 2026 utility bill, all usage-scaled lines and fees included.

## Noise measurement

- **IEC 61672**: the A-weighting curve implemented in `sound_level.py`.
- The Efficienado Reference Box levels (44.6 dB full dial, 33.1 dB half dial, 25.4 dB lowest dial, 24.0 dB room floor) were recorded at 3 ft on 2026-09-07 and anchored to HouseFresh's Winix C545 readings at speeds 2 and 3 recorded in the same position with the same gain (offset 89.1 dB; speeds 1 and 4 give 90.5 and 91.8, so about plus or minus 1.5 dB).
