#!/usr/bin/env python3
"""Build an approximate 1967 mainland Tanzania regional layer.

The script reads modern district polygons from Heed725/Tanzania_Admin_Shapefiles,
assigns each source polygon to its 1967 parent region, dissolves boundaries, and
writes Shapefile, GeoJSON, GeoPackage, CSV crosswalk and a preview PNG.

This is a reconstruction from later administrative geometry, not an official
vectorization of the original 1967 paper map.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import unicodedata
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

EXPECTED_1967 = {
    "ARUSHA",
    "COAST",
    "DODOMA",
    "IRINGA",
    "KIGOMA",
    "KILIMANJARO",
    "MARA",
    "MBEYA",
    "MOROGORO",
    "MTWARA",
    "MWANZA",
    "RUVUMA",
    "SHINYANGA",
    "SINGIDA",
    "TABORA",
    "TANGA",
    "WEST LAKE",
}

CURRENT_REGION_NAMES = {
    "ARUSHA", "DAR ES SALAAM", "DODOMA", "GEITA", "IRINGA", "KAGERA",
    "KATAVI", "KIGOMA", "KILIMANJARO", "LINDI", "MANYARA", "MARA",
    "MBEYA", "MOROGORO", "MTWARA", "MWANZA", "NJOMBE", "PWANI",
    "RUKWA", "RUVUMA", "SHINYANGA", "SIMIYU", "SINGIDA", "SONGWE",
    "TABORA", "TANGA",
}

ZANZIBAR_TOKENS = {
    "KASKAZINI PEMBA", "KUSINI PEMBA", "KASKAZINI UNGUJA", "KUSINI UNGUJA",
    "MJINI MAGHARIBI", "PEMBA NORTH", "PEMBA SOUTH", "ZANZIBAR NORTH",
    "ZANZIBAR SOUTH", "ZANZIBAR WEST", "UNGUJA NORTH", "UNGUJA SOUTH",
}

DIRECT_REGION_MAP = {
    "ARUSHA": "ARUSHA",
    "MANYARA": "ARUSHA",
    "DAR ES SALAAM": "COAST",
    "PWANI": "COAST",
    "DODOMA": "DODOMA",
    "IRINGA": "IRINGA",
    "NJOMBE": "IRINGA",
    "KIGOMA": "KIGOMA",
    "KILIMANJARO": "KILIMANJARO",
    "MARA": "MARA",
    "MBEYA": "MBEYA",
    "SONGWE": "MBEYA",
    "RUKWA": "MBEYA",
    "MOROGORO": "MOROGORO",
    "LINDI": "MTWARA",
    "MTWARA": "MTWARA",
    "MWANZA": "MWANZA",
    "RUVUMA": "RUVUMA",
    "SHINYANGA": "SHINYANGA",
    "SINGIDA": "SINGIDA",
    "KATAVI": "TABORA",
    "TABORA": "TABORA",
    "TANGA": "TANGA",
    "KAGERA": "WEST LAKE",
}


def norm(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def choose_source_shapefile(source: Path) -> Path:
    preferred = [
        source / "District_Unsegmented_2017.shp",
        source / "District_Council.shp",
    ]
    for path in preferred:
        if path.exists():
            return path
    candidates = sorted(source.glob("*District*.shp")) + sorted(source.glob("*.shp"))
    if not candidates:
        raise FileNotFoundError(f"No shapefile found in {source}")
    return candidates[0]


def detect_region_column(gdf: gpd.GeoDataFrame) -> str:
    preferred = [
        "REGION", "Region", "region", "REGION_NAM", "REGION_NAME", "REGNAME",
        "NAME_1", "ADM1_NAME", "ADM1_EN", "mkoa", "MKOA",
    ]
    for col in preferred:
        if col in gdf.columns:
            vals = {norm(v) for v in gdf[col].dropna().unique()}
            if len(vals & CURRENT_REGION_NAMES) >= 8:
                return col

    best_col = None
    best_score = -1
    for col in gdf.columns:
        if col == gdf.geometry.name:
            continue
        if not (pd.api.types.is_object_dtype(gdf[col]) or pd.api.types.is_string_dtype(gdf[col])):
            continue
        vals = {norm(v) for v in gdf[col].dropna().unique()}
        score = len(vals & CURRENT_REGION_NAMES)
        if score > best_score:
            best_col, best_score = col, score
    if best_col is None or best_score < 5:
        raise RuntimeError(f"Could not reliably detect a region field. Columns: {list(gdf.columns)}")
    return best_col


def detect_unit_column(gdf: gpd.GeoDataFrame, region_col: str) -> str:
    preferred = [
        "DISTRICT", "District", "district", "DIST_NAME", "DISTRICT_N",
        "COUNCIL", "Council", "council", "LGA", "LGA_NAME", "NAME_2",
        "ADM2_NAME", "ADM2_EN", "WILAYA", "wilaya",
    ]
    for col in preferred:
        if col in gdf.columns and col != region_col:
            return col

    keywords = {
        "CHATO", "BUKOMBE", "MBOGWE", "NYANGHWALE", "GEITA", "BUSEGA",
        "BARIADI", "MASWA", "MEATU", "ITILIMA", "MAGU", "MPANDA",
        "SUMBAWANGA", "NKASI",
    }
    best_col = None
    best_score = -1
    for col in gdf.columns:
        if col in {region_col, gdf.geometry.name}:
            continue
        if not (pd.api.types.is_object_dtype(gdf[col]) or pd.api.types.is_string_dtype(gdf[col])):
            continue
        vals = [norm(v) for v in gdf[col].dropna().unique()]
        score = sum(any(k in v for k in keywords) for v in vals)
        if score > best_score:
            best_col, best_score = col, score
    if best_col is None:
        raise RuntimeError("Could not detect district/council field")
    return best_col


def assign_1967(region_value: object, unit_value: object) -> str | None:
    region = norm(region_value)
    unit = norm(unit_value)

    if any(token == region or token in region for token in ZANZIBAR_TOKENS):
        return None

    if region == "GEITA":
        # Geita Region was assembled from areas formerly in Kagera, Mwanza and Shinyanga.
        if "CHATO" in unit:
            return "WEST LAKE"
        if "BUKOMBE" in unit or "MBOGWE" in unit:
            return "SHINYANGA"
        # Geita, Nyang'hwale and other descendants of old Geita District -> Mwanza.
        return "MWANZA"

    if region == "SIMIYU":
        # Busega was carved from Magu (Mwanza); the other Simiyu districts trace to Shinyanga.
        if "BUSEGA" in unit:
            return "MWANZA"
        return "SHINYANGA"

    return DIRECT_REGION_MAP.get(region)


def title_case_region(name: str) -> str:
    return name.title().replace("West Lake", "West Lake")


def clean_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    try:
        invalid = ~gdf.geometry.is_valid
        if invalid.any():
            gdf.loc[invalid, "geometry"] = gdf.loc[invalid, "geometry"].buffer(0)
    except Exception:
        pass
    return gdf


def write_outputs(result: gpd.GeoDataFrame, crosswalk: pd.DataFrame, root: Path) -> None:
    data_dir = root / "data"
    dist_dir = root / "dist"
    docs_dir = root / "docs"
    for d in (data_dir, dist_dir, docs_dir):
        d.mkdir(parents=True, exist_ok=True)

    stem = "Tanzania_Regions_1967"

    # Remove previous generated shapefile components so stale sidecars cannot survive.
    for old in data_dir.glob(f"{stem}.*"):
        old.unlink()

    shp_path = data_dir / f"{stem}.shp"
    geojson_path = data_dir / f"{stem}.geojson"
    gpkg_path = data_dir / f"{stem}.gpkg"

    result.to_file(shp_path, driver="ESRI Shapefile", encoding="UTF-8")
    result.to_file(geojson_path, driver="GeoJSON")
    result.to_file(gpkg_path, layer="regions_1967", driver="GPKG")
    (data_dir / f"{stem}.cpg").write_text("UTF-8\n", encoding="ascii")

    crosswalk.to_csv(data_dir / "district_to_1967.csv", index=False)

    zip_path = dist_dir / f"{stem}_Shapefile.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for ext in ["shp", "shx", "dbf", "prj", "cpg"]:
            p = data_dir / f"{stem}.{ext}"
            if p.exists():
                zf.write(p, arcname=p.name)

    fig, ax = plt.subplots(figsize=(9, 10))
    result.plot(ax=ax, edgecolor="black", linewidth=0.65)
    for _, row in result.iterrows():
        p = row.geometry.representative_point()
        ax.annotate(row["REGION_1967"], (p.x, p.y), fontsize=6.5, ha="center")
    ax.set_title("Tanzania Mainland Regions — 1967 Reconstruction")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(docs_dir / f"{stem}_preview.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="Path to Tanzania_Admin_Shapefiles checkout")
    parser.add_argument("--output-root", type=Path, default=Path("."), help="Target repository root")
    args = parser.parse_args()

    source_shp = choose_source_shapefile(args.source)
    print(f"Using source: {source_shp}")

    gdf = gpd.read_file(source_shp)
    gdf = clean_geometry(gdf)
    if gdf.empty:
        raise RuntimeError("Source shapefile contains no usable polygons")

    region_col = detect_region_column(gdf)
    unit_col = detect_unit_column(gdf, region_col)
    print(f"Detected region field: {region_col}")
    print(f"Detected district/council field: {unit_col}")

    work = gdf[[region_col, unit_col, gdf.geometry.name]].copy()
    work["SOURCE_REGION"] = work[region_col].map(norm)
    work["SOURCE_UNIT"] = work[unit_col].map(norm)
    work["REGION_1967_KEY"] = [assign_1967(r, u) for r, u in zip(work[region_col], work[unit_col])]

    mainland = work[work["REGION_1967_KEY"].notna()].copy()
    unmapped = mainland[~mainland["REGION_1967_KEY"].isin(EXPECTED_1967)]
    if not unmapped.empty:
        raise RuntimeError(f"Unexpected 1967 assignments: {sorted(unmapped['REGION_1967_KEY'].dropna().unique())}")

    # Detect mainland source polygons that were not mapped at all.
    mapped_source_regions = {norm(k) for k in DIRECT_REGION_MAP} | {"GEITA", "SIMIYU"}
    source_mainland_mask = ~work["SOURCE_REGION"].apply(lambda x: any(z == x or z in x for z in ZANZIBAR_TOKENS))
    unknown_source = sorted(set(work.loc[source_mainland_mask, "SOURCE_REGION"]) - mapped_source_regions - {""})
    if unknown_source:
        raise RuntimeError(f"Unrecognized mainland source region names: {unknown_source}")

    crosswalk = mainland[["SOURCE_REGION", "SOURCE_UNIT", "REGION_1967_KEY"]].drop_duplicates().sort_values(
        ["REGION_1967_KEY", "SOURCE_REGION", "SOURCE_UNIT"]
    )
    crosswalk = crosswalk.rename(columns={"REGION_1967_KEY": "REGION_1967"})
    crosswalk["REGION_1967"] = crosswalk["REGION_1967"].map(title_case_region)

    dissolved = mainland[["REGION_1967_KEY", mainland.geometry.name]].dissolve(by="REGION_1967_KEY", as_index=False)
    dissolved = clean_geometry(dissolved)

    got = set(dissolved["REGION_1967_KEY"])
    missing = EXPECTED_1967 - got
    extra = got - EXPECTED_1967
    if missing or extra or len(dissolved) != 17:
        raise RuntimeError(
            f"Validation failed. Expected 17 regions; got {len(dissolved)}. "
            f"Missing={sorted(missing)} Extra={sorted(extra)}"
        )

    result = dissolved.rename(columns={"REGION_1967_KEY": "REGION_1967"})
    result["REGION_1967"] = result["REGION_1967"].map(title_case_region)
    result["YEAR"] = 1967
    result["COUNTRY"] = "Tanzania Mainland"
    result["METHOD"] = "Historical reconstruction from later district geometry"
    result = result[["REGION_1967", "YEAR", "COUNTRY", "METHOD", result.geometry.name]]

    if result.crs is None:
        print("WARNING: source CRS missing; assigning EPSG:4326", file=sys.stderr)
        result = result.set_crs(4326)
    else:
        result = result.to_crs(4326)

    write_outputs(result, crosswalk, args.output_root)

    print("Built 17-region 1967 reconstruction successfully:")
    for name in sorted(result["REGION_1967"]):
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
