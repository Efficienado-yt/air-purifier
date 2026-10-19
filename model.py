"""Physics and accounting for the air box model.

Everything numeric comes from params.json (P) and fans_data.py (FANS).  Nothing in
this module is hard-coded except physics constants and unit conversions.

Pipeline for one DIY build (see build()):

    fan curve x filter resistance  ->  operating airflow
    airflow x build factor x media catch  ->  CADR when new
    media decay + swap-interval optimisation  ->  average CADR over the horizon
    purchase + later filter sets + electricity  ->  five-year cost
    five-year cost / average CADR  ->  dollars per average delivered cfm (the ranking metric)

Appliances and kits go through appliance() and kit() so every row lands on the same metric.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "params.json")))

from fans_data import FANS  # noqa: E402  (fans_data reads params.json too)

INWC_TO_PA = 248.84
MMH2O_TO_PA = 9.807
CFM_TO_M3H = 1.699


# ---------------------------------------------------------------------------
# Filter resistance and operating point
# ---------------------------------------------------------------------------
def dp_pa(v_fpm, ftype="MERV13", depth_in=1):
    """Filter pressure drop (Pa) at nominal face velocity v_fpm for a media type and pleat depth.

    The MERV 13 polynomial (Nukit FilterBoxBuilder methodology) takes airflow over an effective
    media area that grows with pleat depth, so the nominal face velocity is divided by
    P["dp_area_factor_by_depth"] (1.0 for a 1 inch pleat) before it is applied.
    """
    kind = P["filter_types"][ftype]["dp"]
    v_fpm = v_fpm / P["dp_area_factor_by_depth"][str(int(depth_in))]
    nukit = (4.73e-7 * v_fpm ** 2 + 3.38e-4 * v_fpm) * INWC_TO_PA
    if kind == "nukit":
        return nukit
    if kind == "nukit_x2":
        return 2 * nukit
    if kind == "nukit_x1.3":
        return 1.3 * nukit
    if kind == "nukit_x0.73":
        return 0.73 * nukit
    if kind == "nukit_x0.95":
        return 0.95 * nukit
    if kind == "hepa_linear":
        return P["hepa_dp_pa_per_100fpm"] * v_fpm / 100.0
    raise ValueError(f"unknown dp model {kind!r}")


def op_point(qmax_cfm, pmax_pa, face_sqft, ftype="MERV13", depth_in=1):
    """Airflow (cfm) where a straight-line fan curve (qmax at 0 Pa, 0 at pmax) crosses the filter curve."""
    if pmax_pa <= 0:
        return 0.0
    lo, hi = 0.0, qmax_cfm
    for _ in range(50):
        q = (lo + hi) / 2
        if qmax_cfm * (1 - dp_pa(q / face_sqft, ftype, depth_in) / pmax_pa) > q:
            lo = q
        else:
            hi = q
    return q


def elec_usd_per_year(watts):
    return watts * P["hours_per_year"] / 1000 * P["electricity_rate_usd_per_kwh"]


def db_3ft(bench_db):
    """Convert a fan-bench (Cybenetics chamber) sum to an estimated in-room level at 3 ft."""
    return bench_db + P["noise"]["bench_to_3ft_offset_db"]


# ---------------------------------------------------------------------------
# Media decay and swap economics
# ---------------------------------------------------------------------------
def tau_months(ftype, scenario, media_sqft, airflow_cfm, s):
    """Decay time constant for a build: tau_ref scaled by (media per cfm / reference) ** s."""
    d = P["filter_types"][ftype]["decay"]
    ratio = (media_sqft / max(airflow_cfm, 1e-9)) / P["filter_life"]["decay"]["media_per_cfm_ref_sqft"]
    return d["tau_ref_months"][scenario] * ratio ** s


def avg_catch_fraction(L_months, tau, floor):
    """Average of floor + (1 - floor) * exp(-t / tau) over 0..L, as a fraction of the new catch."""
    if L_months <= 0 or floor >= 1.0:
        return 1.0
    return floor + (1 - floor) * tau / L_months * (1 - math.exp(-L_months / tau))


def horizon_catch_fraction(L_months, tau, floor, years=None):
    """Average catch over the whole horizon: full swap cycles of L plus the partial last cycle on a fresher filter."""
    H = 12 * (years or P["years"])
    swaps = max(0, math.floor(H / L_months - 1e-9))
    rem = H - swaps * L_months
    return (swaps * L_months * avg_catch_fraction(L_months, tau, floor) + rem * avg_catch_fraction(rem, tau, floor)) / H


def cost_per_cfm(L_months, buy, set_cost, watts, cadr_new, tau, floor, years=None):
    """Return (dollars per average cfm, average delivered cfm, total dollars) for a swap interval L."""
    years = years or P["years"]
    swaps = max(0, math.floor(12 * years / L_months - 1e-9))   # sets after the first, which is in buy
    total = buy + swaps * set_cost + years * elec_usd_per_year(watts)
    delivered = cadr_new * horizon_catch_fraction(L_months, tau, floor, years)
    return total / delivered, delivered, total


def optimize_swap(buy, set_cost, watts, cadr_new, tau, floor, max_L=None):
    """Swap interval (months, 0.5 to max_L in half-month steps) that minimises dollars per average delivered cfm."""
    best = None
    max_L = max_L or 12 * P["years"]
    for L in [x / 2 for x in range(1, 2 * max_L + 1)]:
        c, dlv, tot = cost_per_cfm(L, buy, set_cost, watts, cadr_new, tau, floor)
        if best is None or c < best["ppc"]:
            best = dict(L=L, ppc=c, avg_cadr=dlv, total=tot)
    return best


def n_swaps(L_months, years=None):
    """Filter sets bought after the first one, inside the horizon."""
    return max(0, math.floor(12 * (years or P["years"]) / L_months - 1e-9))


def apply_swap(r, ft, max_L=None):
    """Optimise the swap interval for row r in place; fills life, swaps, avg_cadr, filters_usd_yr, five, ppc."""
    b = optimize_swap(r["buy"], r["set_cost"], r["w"], r["cadr"], r["tau"], ft["decay"]["floor"], max_L or ft.get("max_swap_months"))
    swaps = n_swaps(b["L"])
    r.update(life=b["L"], swaps=swaps, avg_cadr=b["avg_cadr"], filters_usd_yr=swaps * r["set_cost"] / P["years"],
             five=b["total"], ppc=b["ppc"])
    return r


# ---------------------------------------------------------------------------
# Pack pricing
# ---------------------------------------------------------------------------
def pack_cost(n_needed, packs, single=None):
    """Cheapest cost of at least n_needed units from pack options [[count, price, note], ...]; spares are paid for.

    Falls back to n_needed x single when no packs are listed.
    """
    opts = [(int(c), float(p)) for c, p, *_ in packs] if packs else []
    if not opts and single is not None:
        opts.append((1, float(single)))
    if not opts:
        raise ValueError("no price")
    best = [0.0] + [float("inf")] * n_needed
    for n in range(1, n_needed + 1):
        for c, p in opts:
            best[n] = min(best[n], best[max(0, n - c)] + p)
    return best[n_needed]


def fan_cost(fan_name, n_fans):
    f = FANS[fan_name]
    return pack_cost(n_fans, P.get("fan_packs", {}).get(fan_name), f["price"])


def wiring_cost(fan_name, n_fans):
    """Extra dollars to power more fans than the controller has outputs.

    Nothing for daisy-chaining PST fans; otherwise the cheapest splitter option that covers n_fans,
    or a second controller, whichever is less.
    """
    outs = P.get("controller_outputs", 99)
    if n_fans <= outs or FANS[fan_name].get("pst"):
        return 0.0
    opts = [c for cover, c in P.get("splitters", {}).get("options", []) if cover >= n_fans]
    second = P["controller_usd"] * (math.ceil(n_fans / outs) - 1)
    return min(opts + [second])


def filter_spec(name):
    """(width in, height in, depth in, legacy single price, media type, source) for a filter."""
    w, h, d, price, ftype, src = P["filters"][name]
    return w, h, d, price, ftype, src


def filter_set_cost(filter_name, k):
    w, h, d, price, ftype, src = filter_spec(filter_name)
    return pack_cost(k, P.get("filter_packs", {}).get(filter_name), price)


# ---------------------------------------------------------------------------
# Rows: DIY builds, kits, appliances
# ---------------------------------------------------------------------------
def build(fan_name, n_fans, filter_name, k_filters, pwm_index, scenario="average", s=None, build_factor=None):
    """One DIY build: n_fans of fan_name at speed step pwm_index on k_filters of filter_name."""
    s = P["filter_life"]["decay"]["sensitivity_default"] if s is None else s
    build_factor = build_factor or P["build_factor"]
    f = FANS[fan_name]
    w, h, d, price, ftype, src = filter_spec(filter_name)
    ft = P["filter_types"][ftype]
    face = k_filters * w * h / 144.0
    media = face * P["media_sqft_per_face_sqft_by_depth"][str(int(d))]
    qmax = n_fans * f["cfm"][pwm_index]
    pmax = f["mm"][pwm_index] * MMH2O_TO_PA
    q = op_point(qmax, pmax, face, ftype, d)
    cadr = q * build_factor * ft["catch"]
    db_bench = f["db"][pwm_index] + 10 * math.log10(n_fans)
    watts = n_fans * f["w"][pwm_index] + P["controller_watts"]
    set_cost = filter_set_cost(filter_name, k_filters)
    buy = fan_cost(fan_name, n_fans) + wiring_cost(fan_name, n_fans) + set_cost + P["controller_usd"] + P["tape_usd"]
    r = dict(kind="DIY", fan=fan_name, N=n_fans, filt=filter_name, ftype=ftype, k=k_filters, pwm=f["steps"][pwm_index],
             q=q, v=q / face, dp=dp_pa(q / face, ftype, d), cadr=cadr, db_bench=db_bench, db=db_3ft(db_bench), w=watts,
             buy=buy, set_cost=set_cost, face=face, media=media, est=f.get("estimated", False), s=s, scenario=scenario, note="")
    if cadr <= 0:
        r.update(life=0, swaps=0, avg_cadr=0, filters_usd_yr=0, five=0, ppc=float("inf"), upfront=float("inf"), tau=0, cfm_per_w=0)
        return r
    tau = tau_months(ftype, scenario, media, q, s)
    r.update(tau=tau, upfront=buy / cadr, cfm_per_w=cadr / watts)
    apply_swap(r, ft)
    return r


def kit(name, scenario="average", s=None):
    """A commercial kit: the same physics as a DIY build, at the kit's price plus filters and a PSU if needed."""
    K = P["kits"][name]
    f = FANS[K["fan"]]
    r = build(K["fan"], K["N"], K["filter"], K["k"], f["steps"].index(K["pwm"]), scenario, s, build_factor=P.get("build_factor_kit"))
    ft = P["filter_types"][r["ftype"]]
    r["buy"] = K["buy"] + r["set_cost"] + (P["psu_usd"] if K.get("add_psu") else 0)
    r["kind"] = "Kit (modeled)"
    r["note"] = K["note"]
    r["fan"] = name
    if r["cadr"] <= 0:
        return r
    r["upfront"] = r["buy"] / r["cadr"]
    apply_swap(r, ft)
    return r


def appliance(name, scenario="average", s=None):
    """An appliance at its quiet speed.

    Price includes the first filter set; later sets are billed yearly unless appliance_options says otherwise.
    Average CADR = new CADR x the HEPA loading derate, or the model's own electret decay for electret-media rows.
    """
    price, w, cadr, filt, db, note = P["appliances"][name]
    opt = P.get("appliance_options", {}).get(name, {})
    yrs = P["years"]
    later = opt.get("later_sets", yrs - 1)
    sets_in_box = opt.get("sets_in_box", 1)
    life = opt.get("filter_months", 12)
    ftype = "HEPA (mechanical)"
    tau = None
    derate = P["appliance_loading_derate_avg_cadr"][scenario]
    if "electret" in opt:
        e = opt["electret"]
        ftype = e["media"] + " (electret, yearly)"
        s = P["filter_life"]["decay"]["sensitivity_default"] if s is None else s
        media = e["face_sqft"] * P["media_sqft_per_face_sqft_by_depth"]["1"]
        tau = tau_months(e["media"], scenario, media, e["airflow_cfm"], s)
        derate = horizon_catch_fraction(e["swap_months"], tau, P["filter_types"][e["media"]]["decay"]["floor"])
    avg = cadr * derate
    later_usd = opt.get("later_filters_usd", later * filt)   # parts bought inside the horizon when the cadence is not yearly
    five = price + later_usd + yrs * elec_usd_per_year(w)
    return dict(kind="Appliance", fan=name, N=1, filt="OEM or generic, yearly", ftype=ftype, k=1, pwm="quiet speed",
                cadr=cadr, avg_cadr=avg, db_bench=None, db=db, w=w, buy=price, set_cost=filt, life=life, swaps=later,
                sets_in_box=sets_in_box, filters_usd_yr=later_usd / yrs, five=five, ppc=five / avg, upfront=price / cadr,
                cfm_per_w=cadr / w, est=False, note=note, media=None, tau=tau, q=None, v=None, dp=None, s=s,
                scenario=scenario, face=None, derate=derate)


def all_builds(scenario="average", s=None, fans=None):
    """Enumerate every DIY build: fan x fan count x filter x filter count x speed step, subject to the fit and power rules."""
    E = P["enumeration"]
    rows = []
    for fname, f in FANS.items():
        if fans and fname not in fans:
            continue
        for N in E["fans_per_box"]:
            if f.get("fixed_N") and N != f["fixed_N"]:
                continue
            for filt in P["filters"]:
                if filt.startswith("_"):
                    continue
                if f.get("fixed_filters") and filt not in f["fixed_filters"]:
                    continue   # the Reference Box only exists on its own filters
                w, h, d, price, ftype, src = filter_spec(filt)
                for k in E["filters_per_box"]:
                    if f.get("fixed_k") and k != f["fixed_k"]:
                        continue
                    # the fan plate: one filter's face for a cube (k = 4), else the filter face itself
                    plate = (w * w) if k == 4 else (w * h)
                    fansize = f["size"] / 25.4   # frame side in inches
                    if N * fansize * fansize > plate * 0.9:
                        continue
                    for i in range(len(f["steps"])):
                        if f["db"][i] <= 6.0 and not f.get("measured"):
                            continue   # at or below the Cybenetics chamber floor, unmeasurable
                        r = build(fname, N, filt, k, i, scenario, s)
                        if P.get("controller_max_watts") and r["w"] - P["controller_watts"] > P["controller_max_watts"]:
                            continue
                        if r["cadr"] >= E["min_cadr_cfm"]:
                            rows.append(r)
    return rows


# ---------------------------------------------------------------------------
# Rooms: stack units to a target air-change rate
# ---------------------------------------------------------------------------
def room_plan(r, room):
    """How many units of row r reach the room's target ACH, and what that costs and sounds like."""
    vol = P["rooms"][room]["volume_cuft"]
    target = P["rooms"][room]["target_each"] * vol / 60.0
    if not r["avg_cadr"] or r["avg_cadr"] <= 0:
        return None
    units = math.ceil(target / r["avg_cadr"])
    return dict(units=units, cfm=units * r["avg_cadr"], db=r["db"] + 10 * math.log10(units), five=units * r["five"],
                target=target, each=60 * units * r["avg_cadr"] / vol)
