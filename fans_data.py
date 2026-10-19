"""Fan performance curves and per-fan prices.

Each entry in FANS describes one fan at a list of speed steps:

    steps   speed setting for each entry (percent; PWM duty for bench-tested fans,
            fraction of full speed for the estimated and measured entries below)
    cfm     airflow at free delivery
    mm      static pressure, mm H2O
    w       electrical input power, W
    db      noise, dBA, on the Cybenetics chamber scale (one fan)
    price   single-unit price, US$ (superseded by params.json fan_packs where listed)
    pnote   where the price came from
    size    frame size, mm
    pst     True for Arctic PWM Sharing Technology fans, which daisy-chain without a splitter
    estimated   True when the curve is built from a spec sheet rather than bench data
    measured    True for the Efficienado Reference Box, whose noise was measured in a room

Bench curves: Cybenetics PWM-step measurements (10% to 100%), accessed 2026-09-07.
Prices: read 2026-09-07 at the stores named in each pnote.
"""
import json
import math
import os

STEPS10 = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

FANS = {
    'Arctic P12 PWM PST (120)': dict(steps=STEPS10, pst=True,
        cfm=[6.37, 10.01, 16.38, 22.11, 27.71, 33.11, 38, 42.47, 47.82, 52.15],
        mm=[0.03, 0.1, 0.24, 0.42, 0.63, 0.86, 1.07, 1.29, 1.53, 1.76],
        w=[0.24, 0.26, 0.31, 0.38, 0.48, 0.59, 0.72, 0.88, 1.06, 1.25],
        db=[6.5, 9.9, 12.3, 13.6, 15.5, 16.5, 21, 22, 25.1, 28.6],
        price=11.99, pnote='Arctic US single MSRP 2026-09-07, out of stock that day (5-pack MSRP $34.99 also out; Newegg 5-pack $80.41 = $16.08 in stock); price policy in params _price_policy', size=120),
    'Arctic P14 PWM PST (140)': dict(steps=STEPS10[1:], pst=True,
        cfm=[16.19, 23.28, 31.25, 39.21, 46.22, 51.91, 58.8, 65.56, 71.9],
        mm=[0.14, 0.31, 0.51, 0.73, 0.97, 1.18, 1.42, 1.69, 1.96],
        w=[0.26, 0.32, 0.42, 0.56, 0.71, 0.89, 1.1, 1.34, 1.6],
        db=[6, 6, 8.8, 14.8, 20, 27.7, 27, 29.6, 31.9],
        price=12.99, pnote='Arctic US single MSRP 2026-09-07, out of stock that day; a Newegg marketplace single (PlatinumMicro, ACFAN00197A) at the same $12.99 was in stock but marketplace listings are excluded by policy; live 5-packs $14.60 to $17.80 a fan', size=140),
    'Arctic P12 Pro (120)': dict(steps=STEPS10,
        cfm=[16.88, 23.49, 29.72, 36.04, 43.33, 49.8, 56.53, 64.02, 70.34, 76.76],
        mm=[0.47, 0.83, 1.32, 1.89, 2.59, 3.4, 4.34, 5.38, 6.29, 6.27],
        w=[0.18, 0.34, 0.56, 0.86, 1.31, 1.91, 2.69, 3.71, 4.73, 4.73],
        # the 10% step reads 1.9 dBA on the Cybenetics chart, below the 6 dBA chamber floor; the model excludes it
        db=[1.9, 9.7, 15.3, 19.8, 24.1, 27.9, 31.8, 34.9, 37.5, 39.7],
        price=16.49, pnote='Arctic US store single, in stock 2026-09-07 (PST 5-pack $44.99 not available)', size=120),
    'Arctic P14 Pro PST (140)': dict(steps=STEPS10, pst=True,
        cfm=[18.26, 27.21, 36.85, 46.44, 55.97, 66.47, 75.55, 86.02, 94.98, 103.78],
        mm=[0.28, 0.6, 1.04, 1.62, 2.3, 3.11, 4.06, 5.08, 5.11, 5.09],
        w=[0.32, 0.46, 0.7, 1.06, 1.6, 2.36, 3.38, 4.75, 4.79, 4.79],
        db=[6, 6, 10.3, 16.6, 22, 26.9, 30.3, 33.8, 36.5, 39],
        price=16.33, pnote='Arctic US single page $16.33, in stock 2026-09-07 (was $15.20 from a Newegg 5-pack of unknown seller; a $12.99 marketplace single is excluded by policy)', size=140),
    'Arctic P12 Max Black (120)': dict(steps=STEPS10,
        cfm=[19.21, 27.08, 35.82, 43.44, 54.28, 59.75, 67.01, 72.59, 79.71, 85.02],
        mm=[0.42, 0.74, 1.2, 1.69, 2.31, 2.88, 3.42, 3.88, 4.51, 5.12],
        w=[0.34, 0.44, 0.64, 0.89, 1.28, 1.69, 2.16, 2.62, 3.29, 4.03],
        db=[6, 13.8, 19.3, 24.7, 28.9, 33.8, 36.3, 38, 39.9, 42],
        price=17.99, pnote='single MSRP, not available', size=120),
    'Arctic P14 Max (140)': dict(steps=STEPS10,
        cfm=[22.4, 35.42, 47.77, 62.59, 71.85, 80.99, 91.21, 98.69, 108.61, 113.7],
        mm=[0.28, 0.61, 1.04, 1.61, 2.03, 2.47, 2.89, 3.25, 3.87, 4.11],
        w=[0.12, 0.31, 0.6, 1.08, 1.54, 2.06, 2.59, 3.24, 4.25, 4.81],
        db=[6, 8.4, 17.5, 23.1, 29.3, 31.9, 34.2, 37.1, 38.6, 40.5],
        price=15.99, pnote='Arctic US store single MSRP (out of stock); Newegg first-party single $18.70 (qty 3); a $10.99 marketplace single (Platinum Micro) exists but is excluded by the price policy, see params _price_policy', size=140),
    'Noctua NF-A12x25 G2 (120)': dict(steps=STEPS10,
        cfm=[11.28, 11.08, 16.7, 22.93, 29.18, 35.24, 41.36, 48.07, 55.08, 60.24],
        mm=[0.12, 0.12, 0.26, 0.47, 0.78, 1.04, 1.4, 1.73, 2.34, 2.75],
        w=[0.19, 0.2, 0.26, 0.35, 0.46, 0.61, 0.82, 1.09, 1.5, 1.9],
        db=[6, 6, 6, 6, 9.4, 15.5, 19.1, 23.9, 26.5, 29.8],
        price=32.48, pnote='2-pack $64.95 Newegg', size=120),
    'Noctua NF-A12x25 (120)': dict(steps=STEPS10,
        cfm=[0.15, 8.13, 16.23, 22.94, 29.08, 35.38, 41.23, 46.85, 51.56, 56.11],
        mm=[0.01, 0.07, 0.23, 0.45, 0.69, 0.94, 1.27, 1.60, 1.92, 2.26],
        w=[0.12, 0.17, 0.24, 0.32, 0.44, 0.60, 0.78, 1.01, 1.24, 1.50],
        db=[6, 6, 6, 7.7, 14, 19.3, 23, 26.4, 29, 31.3],
        price=38.79, pnote='single Newegg', size=120),
    'Noctua NF-F12 (120)': dict(steps=STEPS10[2:],
        cfm=[4.24, 12.47, 20.41, 25.57, 31.96, 37.33, 41.69, 45.73],
        mm=[0.1, 0.27, 0.49, 0.72, 0.96, 1.25, 1.53, 1.83],
        w=[0.29, 0.32, 0.38, 0.47, 0.56, 0.67, 0.79, 0.94],
        db=[6, 6, 12.1, 16.7, 22, 23.1, 27.3, 28.6],
        price=27.59, pnote='single Newegg', size=120),
    'Noctua NF-A14x25 G2 (140)': dict(steps=[20, 30, 40, 50, 60, 70, 80, 90, 100],
        cfm=[16.86, 23.6, 33.42, 43.44, 52.04, 63.68, 73.53, 83.83, 94.59],
        mm=[0.06, 0.22, 0.38, 0.63, 0.84, 1.19, 1.62, 2.08, 2.51],
        w=[0.13, 0.22, 0.34, 0.52, 0.8, 1.19, 1.7, 2.45, 3.35],
        db=[6, 6, 7.2, 12, 17, 21.9, 25.1, 28.8, 32.4],
        price=47.43, pnote='2-pack $94.85 Newegg', size=140),
    'Noctua NF-P14s redux-1200 (140)': dict(steps=STEPS10,
        cfm=[0.1, 0.57, 12.36, 23.72, 32.56, 42.57, 50.12, 56.41, 62.45, 68.2],
        mm=[0.0, 0.02, 0.11, 0.26, 0.4, 0.55, 0.72, 0.98, 1.09, 1.33],
        w=[0.14, 0.24, 0.3, 0.35, 0.46, 0.58, 0.72, 0.91, 1.09, 1.31],
        db=[6, 6, 6, 7.3, 13.8, 18.9, 23.1, 25.8, 29.1, 32],
        price=22.79, pnote='single Newegg', size=140),
    'Phanteks T30-120 Advanced mode (120x30)': dict(steps=STEPS10,
        cfm=[8.33, 18.86, 29.2, 39.1, 50.09, 59.76, 69.82, 81.69, 94.04, 105.17],
        mm=[0.07, 0.26, 0.57, 0.97, 1.48, 2.1, 2.86, 3.75, 4.78, 6.37],
        w=[0.26, 0.35, 0.44, 0.65, 0.94, 1.32, 1.82, 2.52, 3.47, 5.14],
        db=[6, 6, 7.4, 15.2, 22.3, 27.6, 33, 36.8, 39.5, 43.6],
        price=32.53, pnote='3-pack $97.59 Newegg', size=120),
    'be quiet! Silent Wings 4 120': dict(steps=STEPS10[1:],
        cfm=[9.07, 13.73, 19.23, 22.35, 26.61, 31.39, 36.69, 40.55, 44.91],
        mm=[0.08, 0.2, 0.28, 0.39, 0.52, 0.69, 0.88, 1.04, 1.28],
        w=[0.2, 0.24, 0.3, 0.37, 0.42, 0.52, 0.65, 0.8, 0.95],
        db=[6, 6, 6, 6, 6.3, 11.3, 15.9, 19.5, 22.3],
        price=24.90, pnote='single Newegg', size=120),
    'be quiet! Silent Wings 4 140': dict(steps=STEPS10[2:],
        cfm=[16.54, 21.93, 27.04, 31.74, 36.26, 41.32, 45.42, 49.97],
        mm=[0.12, 0.23, 0.29, 0.37, 0.49, 0.62, 0.72, 0.8],
        w=[0.22, 0.25, 0.3, 0.35, 0.42, 0.49, 0.59, 0.7],
        db=[6, 6, 6, 6, 7.3, 12.1, 15, 18.6],
        price=24.90, pnote='single Newegg', size=140),
    'be quiet! Silent Wings 4 140 high-speed': dict(steps=STEPS10,
        cfm=[1.64, 14.34, 24.39, 32.05, 40.96, 47.86, 56.64, 64.19, 73.35, 80.58],
        mm=[0.01, 0.09, 0.25, 0.45, 0.67, 0.85, 1.12, 1.42, 1.72, 2.03],
        w=[0.04, 0.1, 0.19, 0.34, 0.49, 0.66, 0.92, 1.22, 1.57, 1.93],
        db=[6, 6, 6, 9, 15.8, 21.5, 25.8, 29, 33.6, 35.7],
        price=24.50, pnote='single Newegg 2026-09-07', size=140),
    'be quiet! Pure Wings 3 120 high-speed': dict(steps=STEPS10,
        cfm=[7.07, 10.52, 16.7, 22.85, 29.4, 35.13, 41.52, 47.23, 53.89, 60.45],
        mm=[0.04, 0.09, 0.2, 0.37, 0.58, 0.83, 1.13, 1.48, 1.86, 2.27],
        w=[0.08, 0.12, 0.19, 0.29, 0.42, 0.62, 0.89, 1.26, 1.78, 2.38],
        db=[6, 7.5, 10.6, 13, 15.5, 19.5, 24, 27.1, 30.6, 33.2],
        price=13.99, pnote='single Newegg', size=120),
    'be quiet! Pure Wings 3 140 high-speed': dict(steps=STEPS10[1:],
        cfm=[14.42, 20.55, 28.34, 34.95, 42.34, 49.81, 57.56, 64.88, 71.64],
        mm=[0.11, 0.22, 0.39, 0.6, 0.85, 1.17, 1.53, 1.97, 2.33],
        w=[0.24, 0.29, 0.38, 0.52, 0.74, 1.07, 1.55, 2.2, 2.96],
        db=[6, 6, 9, 15.3, 20.6, 24.7, 28.8, 31.8, 34.2],
        price=11.63, pnote='3-pack $34.90 Newegg', size=140),
}

# ---------------------------------------------------------------------------
# Estimated fan: Noctua NF-P12 redux-1700
#
# The NF-P12 redux has no Cybenetics entry, so its curve is built from the
# datasheet with the fan laws at a fraction r of full speed: airflow scales
# with r, pressure with r^2, power with r^3, noise as 50 log(r).  Steps are
# percent of full speed (a voltage dial), not PWM duty.
#
# Noise is Noctua's 1 m bench figure plus 8.7 dB to approximate the Cybenetics
# chamber scale.  The 8.7 dB is the offset observed on the NF-A12x25 (Noctua
# 22.6 dB(A) at 2000 rpm vs Cybenetics 31.3 dBA at 2134 rpm); about 1.4 dB of
# it is that speed difference, so the true bench-to-bench offset is nearer
# 7.3 dB and these rows are about 1.4 dB pessimistic.  ESTIMATE, flagged.
#
# Datasheet (noctua.at, confirmed 2026-09-16): 70.75 cfm, 2.83 mm H2O,
# 25.1 dB(A), 1.08 W maximum input power.
# ---------------------------------------------------------------------------
NFP12_CFM, NFP12_MM, NFP12_W, NFP12_DB = 70.75, 2.83, 1.08, 25.1

# Noctua NF-A14 FLX at 1200 rpm (datasheet): 115.5 m3/h, 1.51 mm H2O, 19.2 dB(A), 0.96 W maximum.
NFA14_CFM, NFA14_MM, NFA14_W = 68.0, 1.51, 0.96


def make_nfp12(price, pnote):
    """Spec-sheet pseudo-curve for the NF-P12 redux-1700 at 30% to 100% of full speed."""
    steps, cfm, mm, w, db = [], [], [], [], []
    for s in range(30, 101, 10):
        r = s / 100.0
        steps.append(s)
        cfm.append(NFP12_CFM * r)
        mm.append(NFP12_MM * r * r)
        w.append(max(0.1, NFP12_W * r ** 3))
        db.append(NFP12_DB + 50 * math.log10(r) + 8.7)
    return dict(steps=steps, cfm=cfm, mm=mm, w=w, db=db, price=price, pnote=pnote, size=120, estimated=True)


FANS['Noctua NF-P12 redux-1700 (Jan 2026 price $14.95) EST'] = make_nfp12(
    14.95, 'Amazon price Jan 2026; curve and noise estimated from spec')
FANS['Noctua NF-P12 redux-1700 (2026-09-07 price) EST'] = make_nfp12(
    16.45, 'Amazon single $16.45, read 2026-09-07 (fan_packs); curve and noise estimated from spec')


# ---------------------------------------------------------------------------
# Efficienado Reference Box
#
# A real four-fan box: three NF-P12 redux-1700 plus one NF-A14 FLX (which only
# starts at 3 to 4 V on the controller), on four 16x25x1 filters, driven by a
# 3 to 12 V voltage dial.  Its noise was MEASURED at 3 ft on 2026-09-07 with a
# recorder anchored to HouseFresh's published Winix C545 readings:
# full dial 44.6 dB, half dial 33.1 dB, lowest dial (A14 not spinning) 25.4 dB,
# room floor 24.0 dB.  Those levels live in params.json under
# noise.reference_box_measured_2026-09-07.
#
# Model: the room floor is subtracted energetically, the half-dial speed
# fraction is located on the 50 log fan law from the full-dial level, and the
# other steps follow the fan law from the measured full dial.  Per-fan values
# are the four-fan totals divided out so the model's "+10 log N + offset"
# reproduces the measured whole-box level.  Airflow and watts come from the
# datasheets by fan law; all four fans are assumed to share the same speed
# fraction at each dial position (the A14 has no separate anchor).
# ---------------------------------------------------------------------------
def make_reference_box():
    here = os.path.dirname(os.path.abspath(__file__))
    M = json.load(open(os.path.join(here, "params.json")))["noise"]["reference_box_measured_2026-09-07"]
    floor = M["room_floor_db"]

    def fan_only(level):
        return 10 * math.log10(10 ** (level / 10) - 10 ** (floor / 10))

    full_db, half_db = fan_only(M["box_full_dial_db"]), fan_only(M["box_half_dial_db"])
    r_half = 10 ** ((half_db - full_db) / 50)      # 12.0 dB drop -> 0.575 of full speed
    s_half = round(100 * r_half)                   # -> 57% of full speed
    steps = sorted(set([30, 40, 50, s_half, 60, 70, 80, 90, 100]))
    full_cfm = 3 * NFP12_CFM + NFA14_CFM
    full_w = 3 * NFP12_W + NFA14_W
    cfm, mm, w, db = [], [], [], []
    for s in steps:
        r = s / 100.0
        cfm.append(full_cfm / 4 * r)
        mm.append((3 * NFP12_MM + NFA14_MM) / 4 * r * r)
        w.append(max(0.1, full_w / 4 * r ** 3))
        # fan law from the measured full dial; reproduces half_db at s_half
        db.append(full_db + 50 * math.log10(r) - 2.0 - 10 * math.log10(4))
    return dict(steps=steps, cfm=cfm, mm=mm, w=w, db=db,
                price=(3 * 14.95) / 4,
                pnote='Efficienado Reference Box as bought: three NF-P12 at $14.95 plus a spare NF-A14 already on hand; '
                      'noise MEASURED 2026-09-07 at the full and half dial (100%% and %d%% of full speed, room floor subtracted), fan law between' % s_half,
                size=120, measured=True, measured_steps=(s_half, 100),
                fixed_N=4, fixed_k=4, fixed_filters=('16x25x1 MERV13', '16x25x1 Filtrete 1900 (reference box)'))


REF_BOX_AS_BOUGHT = 'Efficienado Reference Box (3 NF-P12 + NF-A14) as bought, noise MEASURED'
REF_BOX_TODAY = 'Efficienado Reference Box layout at 2026-09-07 fan price, noise MEASURED'

FANS[REF_BOX_AS_BOUGHT] = make_reference_box()

# The same box priced as a viewer would buy it today: four NF-P12 redux (Amazon 3-pack $49.35 plus a
# single $16.45, read 2026-09-07), no spare on hand.  Airflow, watts and noise identical.
_today = dict(make_reference_box())
_today['price'] = 16.45
_today['pnote'] = ('Reference Box layout at 2026-09-07 fan price, four NF-P12 redux (Amazon 3-pack $49.35 plus a single $16.45); '
                   'noise as measured on the Reference Box')
FANS[REF_BOX_TODAY] = _today
