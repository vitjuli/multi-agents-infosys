from __future__ import annotations

import json

import pandas as pd
import pydeck as pdk
import streamlit as st

from data_centre_site_selector.blueprint_bridge import (
    derive_optimisation_choices_from_blueprint,
)
from data_centre_site_selector.data_analysis import resolve_anchor_region
from data_centre_site_selector.data_paths import CANDIDATE_FEATURES_CSV
from data_centre_site_selector.logging_utils import configure_logging
from data_centre_site_selector.orchestrator import run_site_selection
from data_centre_site_selector.prompt_parser import parse_budget_gbp
from data_centre_site_selector.preprocess import build_candidate_features
from data_centre_site_selector.workload_profiles import workload_profile_options
from src.planning.blueprint_startup import run_blueprint_startup


st.set_page_config(
    page_title="Data Centre Site Selector",
    page_icon="",
    layout="wide",
)

configure_logging()

st.title("UK Data Centre Site Selector")
st.caption(
    "Blueprint-guided startup with the standard planning, ranking, critic, and report pipeline."
)

with st.sidebar:
    st.header("Run Settings")
    prompt = st.text_area(
        "Prompt",
        value="Find the best 5 data centre locations around Manchester for 500 MW compute with a £10bn budget",
        height=140,
    )
    workload = st.selectbox(
        "Workload override",
        options=["Auto-detect", *sorted(workload_profile_options())],
        index=0,
    )
    compute_mw = st.number_input("Compute MW", min_value=0.0, value=500.0, step=10.0)
    budget_text = st.text_input("Budget", value="£10bn")
    region = st.text_input("Region override", value="")
    target_location = st.text_input("Target location", value="")
    target_radius_miles = st.number_input(
        "Target radius miles",
        min_value=0.0,
        value=0.0,
        step=5.0,
        help="Set greater than 0 to filter within a radius of the target location.",
    )
    top_k = st.slider("Top K", min_value=1, max_value=10, value=5)
    optimise = st.multiselect(
        "Optimisation overrides",
        options=[
            "co2",
            "population_strain",
            "political_favour",
            "cost",
            "latency",
            "resilience",
            "land_use",
            "infrastructure",
        ],
        default=[],
    )
    use_blueprint = st.toggle("Use blueprint startup", value=True)
    use_agents = st.toggle("Use OpenAI agents", value=True)
    use_web_policy = st.toggle("Use web policy research", value=False)
    include_pdf = st.toggle("Generate PDF", value=False)
    debug_logs = st.toggle("Debug logs", value=False)
    run_button = st.button("Run Analysis", type="primary")


def _show_blueprint(startup) -> None:
    st.subheader("Blueprint Startup")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Preferences**")
        st.json(startup.preferences.to_dict())
    with col2:
        st.markdown("**Policy Weights**")
        st.json(startup.policy)
    st.markdown("**Blueprint**")
    st.json(startup.blueprint.to_dict())


def _recommendation_frame(result: dict) -> pd.DataFrame:
    rows = []
    for rec in result["site_selection"]["recommendations"]:
        rows.append(
            {
                "location": rec["location"],
                "priority": rec["priority_flag"],
                "feasible": rec["feasibility"],
                "compute_mw": rec["compute_mw"],
                "capex_gbp": rec["estimated_capex_gbp"],
                "opex_gbp": rec["estimated_annual_opex_gbp"],
                "production_score": rec["score_breakdown"]["production"],
                "lat": rec["latitude"],
                "lon": rec["longitude"],
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def _candidate_features() -> pd.DataFrame:
    if CANDIDATE_FEATURES_CSV.exists():
        return pd.read_csv(CANDIDATE_FEATURES_CSV)
    features, _ = build_candidate_features(include_flood=False)
    return features


def _map_context(result: dict) -> tuple[pd.DataFrame, dict | None, float | None]:
    site_selection = result["site_selection"]
    constraints = site_selection.get("constraints", {})
    rec_df = _recommendation_frame(result)
    if rec_df.empty:
        return rec_df, None, None

    anchor_point = None
    anchor_name = constraints.get("resolved_anchor_region") or constraints.get(
        "target_location"
    )
    radius_miles = constraints.get("target_radius_miles")
    if anchor_name:
        features = _candidate_features()
        anchor_row = resolve_anchor_region(features, anchor_name)
        if anchor_row is not None:
            anchor_point = {
                "location": str(anchor_row.get("region", anchor_name)),
                "lat": float(anchor_row["lat"]),
                "lon": float(anchor_row["lon"]),
            }

    if anchor_point is None and constraints.get("region_text"):
        top_rec = rec_df.iloc[0]
        anchor_point = {
            "location": constraints["region_text"],
            "lat": float(top_rec["lat"]),
            "lon": float(top_rec["lon"]),
        }

    return rec_df, anchor_point, radius_miles


def _render_map(result: dict) -> None:
    rec_df, anchor_point, radius_miles = _map_context(result)
    if rec_df.empty:
        st.info("No recommendation coordinates available for map rendering.")
        return

    top = rec_df.iloc[0]
    map_rows = rec_df.copy()
    map_rows["marker_radius"] = map_rows["location"].eq(top["location"]).map(
        lambda is_top: 24000 if is_top else 14000
    )
    map_rows["marker_color"] = map_rows["location"].eq(top["location"]).map(
        lambda is_top: [220, 38, 38, 210] if is_top else [37, 99, 235, 180]
    )
    map_rows["label"] = map_rows.apply(
        lambda row: (
            f"{row['location']}\n"
            f"Production score: {row['production_score']:.2f}\n"
            f"Capex: GBP {row['capex_gbp']:,.0f}"
        ),
        axis=1,
    )

    layers: list[pdk.Layer] = [
        pdk.Layer(
            "ScatterplotLayer",
            data=map_rows,
            get_position="[lon, lat]",
            get_radius="marker_radius",
            get_fill_color="marker_color",
            pickable=True,
            stroked=True,
            get_line_color=[255, 255, 255, 180],
            line_width_min_pixels=1,
        )
    ]

    if anchor_point is not None:
        anchor_df = pd.DataFrame([anchor_point])
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=anchor_df,
                get_position="[lon, lat]",
                get_radius=9000,
                get_fill_color=[16, 185, 129, 220],
                pickable=True,
                stroked=True,
                get_line_color=[15, 23, 42, 220],
                line_width_min_pixels=1,
            )
        )
        if radius_miles and radius_miles > 0:
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=anchor_df,
                    get_position="[lon, lat]",
                    get_radius=float(radius_miles) * 1609.34,
                    get_fill_color=[16, 185, 129, 30],
                    stroked=True,
                    filled=True,
                    get_line_color=[16, 185, 129, 160],
                    line_width_min_pixels=2,
                    pickable=False,
                )
            )

    all_lats = list(map_rows["lat"].astype(float))
    all_lons = list(map_rows["lon"].astype(float))
    if anchor_point is not None:
        all_lats.append(float(anchor_point["lat"]))
        all_lons.append(float(anchor_point["lon"]))

    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    lat_span = max(all_lats) - min(all_lats) if len(all_lats) > 1 else 0.0
    lon_span = max(all_lons) - min(all_lons) if len(all_lons) > 1 else 0.0
    max_span = max(lat_span, lon_span)
    if radius_miles and radius_miles > 0:
        zoom = 8 if radius_miles <= 15 else 7 if radius_miles <= 50 else 6
    elif max_span <= 0.08:
        zoom = 11
    elif max_span <= 0.2:
        zoom = 10
    elif max_span <= 0.5:
        zoom = 9
    else:
        zoom = 8

    st.pydeck_chart(
        pdk.Deck(
            map_provider="carto",
            map_style=pdk.map_styles.CARTO_LIGHT,
            initial_view_state=pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=zoom,
                pitch=0,
            ),
            layers=layers,
            tooltip={
                "text": "{label}" if "label" in map_rows.columns else "{location}"
            },
        ),
        use_container_width=True,
    )

    if anchor_point is not None:
        scope = result["site_selection"]["constraints"].get("region_text") or anchor_point["location"]
        st.caption(
            f"Search scope centred on {anchor_point['location']}"
            + (
                f" with a {radius_miles:.0f}-mile radius."
                if radius_miles and radius_miles > 0
                else f" for region search '{scope}'."
            )
        )


def _render_optimal_location(result: dict) -> None:
    recommendations = result["site_selection"].get("recommendations", [])
    if not recommendations:
        st.info("No recommendation metadata available.")
        return

    optimal = recommendations[0]
    score_breakdown = optimal.get("score_breakdown", {})

    st.markdown("**Optimal Location**")
    st.markdown(f"### {optimal['location']}")
    st.caption(optimal.get("text_summary", ""))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Production Score", f"{score_breakdown.get('production', 0):.2f}")
        st.metric("Compute MW", f"{optimal.get('compute_mw', 0):,.0f}")
        st.metric("Capex", f"GBP {optimal.get('estimated_capex_gbp', 0):,.0f}")
    with col2:
        st.metric("Annual Opex", f"GBP {optimal.get('estimated_annual_opex_gbp', 0):,.0f}")
        st.metric(
            "Coordinates",
            f"{optimal.get('latitude', 0):.4f}, {optimal.get('longitude', 0):.4f}",
        )
        st.metric("Priority", str(optimal.get("priority_flag", "")).title())

    metadata = {
        "feasibility": optimal.get("feasibility"),
        "altitude_m": optimal.get("altitude_m"),
        "policy_points": optimal.get("policy_points", []),
        "grants_tax_breaks": optimal.get("grants_tax_breaks", []),
        "score_breakdown": score_breakdown,
        "explanation": optimal.get("explanation"),
    }
    with st.expander("Optimal location metadata", expanded=True):
        st.json(metadata)


if run_button:
    configure_logging(debug=debug_logs)
    selected_workload = None if workload == "Auto-detect" else workload
    selected_target_location = target_location.strip() or None
    selected_target_radius_miles = (
        target_radius_miles if target_radius_miles > 0 else None
    )
    selected_region = (
        None
        if selected_target_location and selected_target_radius_miles is not None
        else region.strip() or None
    )
    budget_gbp = parse_budget_gbp(budget_text) if budget_text.strip() else None
    optimisation_choices = optimise or None
    startup = None

    if selected_target_location and selected_target_radius_miles is not None and region.strip():
        st.info(
            "Ignoring Region override because Target location + Target radius defines the search scope."
        )

    with st.spinner("Running site selection pipeline..."):
        if use_blueprint:
            startup = run_blueprint_startup(
                prompt,
                use_llm_preferences=use_agents,
                interactive=False,
            )
            if optimisation_choices is None:
                optimisation_choices = (
                    derive_optimisation_choices_from_blueprint(startup) or None
                )
        result = run_site_selection(
            query=prompt,
            workload=selected_workload,
            top_k=top_k,
            model=None,
            use_agents=use_agents,
            budget_gbp=budget_gbp,
            region=selected_region,
            target_location=selected_target_location,
            target_radius_miles=selected_target_radius_miles,
            compute_mw=compute_mw or None,
            optimisation_choices=optimisation_choices,
            enable_web_policy=use_web_policy,
            generate_pdf=include_pdf,
        )

    if startup is not None:
        _show_blueprint(startup)

    st.subheader("Recommendations")
    rec_df = _recommendation_frame(result)
    st.dataframe(rec_df, use_container_width=True, hide_index=True)

    map_col, detail_col = st.columns([1.7, 1])
    with map_col:
        st.markdown("**Search Map**")
        _render_map(result)
    with detail_col:
        _render_optimal_location(result)

    st.subheader("Planner Summary")
    st.json(result["site_selection"])

    st.subheader("Reports")
    report_tabs = st.tabs(["Terminal", "Markdown", "JSON"])
    with report_tabs[0]:
        st.code(result["terminal"])
    with report_tabs[1]:
        st.markdown(result["report_path"].read_text(encoding="utf-8"))
    with report_tabs[2]:
        st.code(json.dumps(result["site_selection"], indent=2, default=str), language="json")
