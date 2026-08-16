#!/usr/bin/env python3
"""Build Tanganyika 1950 province and district GIS layers.

Source: Princeton University Library / NYU Spatial Data Repository
"Tanzania extracted historical administrative boundaries, 1950".
The historical polygons were digitized from a British Colonial Office map.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import zipfile

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


def find_source_shapefile(source_dir: Path) -> Path:
    candidates = list(source_dir.rglob("*.shp"))
    if not candidates:
        raise FileNotFoundError(f"No .shp found under {source_dir}")

    preferred = [p for p in candidates if "1950" in p.name.lower() or "boundaries" in p.name.lower()]
    return preferred[0] if preferred else candidates[0]


def clean_text(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.strip()
        .replace({"-": "", "--": "", "None": "", "nan": ""})
    )


def save_shapefile(gdf: gpd.GeoDataFrame, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_dir / f"{stem}.shp", driver="ESRI Shapefile", encoding="UTF-8")
    (out_dir / f"{stem}.cpg").write_text("UTF-8", encoding="utf-8")


def zip_shapefile(out_dir: Path, stem: str, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    extensions = [".shp", ".shx", ".dbf", ".prj", ".cpg"]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for ext in extensions:
            p = out_dir / f"{stem}{ext}"
            if p.exists():
                zf.write(p, arcname=p.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="source_1950", help="Folder containing extracted Princeton shapefile")
    parser.add_argument("--output", default="data/tanganyika_1950", help="Output folder")
    parser.add_argument("--dist", default="dist", help="Release package folder")
    parser.add_argument("--docs", default="docs", help="Preview folder")
    args = parser.parse_args()

    source_dir = Path(args.source)
    out_dir = Path(args.output)
    dist_dir = Path(args.dist)
    docs_dir = Path(args.docs)

    shp = find_source_shapefile(source_dir)
    print(f"Using source: {shp}")

    gdf = gpd.read_file(shp)
    if gdf.empty:
        raise RuntimeError("Historical source contains no features")

    # Normalize field names while preserving the original historical attributes.
    fields = {c.lower(): c for c in gdf.columns}
    province_col = fields.get("province")
    district_col = fields.get("district")
    if not province_col or not district_col:
        raise RuntimeError(f"Expected Province and District fields. Found: {list(gdf.columns)}")

    gdf["PROVINCE"] = clean_text(gdf[province_col])
    gdf["DISTRICT"] = clean_text(gdf[district_col])

    # Exclude any non-Tanganyika island polygons if they happen to occur in a distribution copy.
    mask = ~gdf["PROVINCE"].str.contains("zanzibar|pemba", case=False, regex=True, na=False)
    gdf = gdf.loc[mask].copy()

    # Fix invalid geometry where possible, then standardize output CRS for GIS use.
    gdf["geometry"] = gdf.geometry.make_valid()
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    gdf = gdf.to_crs(4326)

    districts = gdf[["PROVINCE", "DISTRICT", "geometry"]].copy()
    districts.insert(0, "YEAR", 1950)
    districts.insert(1, "TERRITORY", "Tanganyika")

    provinces = districts.dissolve(by="PROVINCE", as_index=False, aggfunc="first")
    provinces["YEAR"] = 1950
    provinces["TERRITORY"] = "Tanganyika"
    provinces = provinces[["YEAR", "TERRITORY", "PROVINCE", "geometry"]]

    out_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    district_stem = "Tanganyika_Districts_1950"
    province_stem = "Tanganyika_Provinces_1950"

    save_shapefile(districts, out_dir, district_stem)
    save_shapefile(provinces, out_dir, province_stem)

    districts.to_file(out_dir / f"{district_stem}.gpkg", layer="districts_1950", driver="GPKG")
    provinces.to_file(out_dir / f"{province_stem}.gpkg", layer="provinces_1950", driver="GPKG")
    districts.to_file(out_dir / f"{district_stem}.geojson", driver="GeoJSON")
    provinces.to_file(out_dir / f"{province_stem}.geojson", driver="GeoJSON")

    # Human-readable crosswalk/catalogue.
    crosswalk = districts[["PROVINCE", "DISTRICT"]].drop_duplicates().sort_values(["PROVINCE", "DISTRICT"])
    crosswalk.to_csv(out_dir / "Tanganyika_1950_Province_District_Crosswalk.csv", index=False)

    summary = {
        "year": 1950,
        "territory": "Tanganyika",
        "province_count": int(len(provinces)),
        "district_polygon_count": int(len(districts)),
        "provinces": sorted(provinces["PROVINCE"].dropna().astype(str).tolist()),
        "crs": "EPSG:4326",
        "source": "Princeton University Library historical administrative boundaries, digitized from British Colonial Office map",
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    zip_shapefile(out_dir, district_stem, dist_dir / f"{district_stem}_Shapefile.zip")
    zip_shapefile(out_dir, province_stem, dist_dir / f"{province_stem}_Shapefile.zip")

    # Preview with thick province lines over thin district lines, matching the historical-map hierarchy.
    fig, ax = plt.subplots(figsize=(9, 10))
    districts.boundary.plot(ax=ax, linewidth=0.35)
    provinces.boundary.plot(ax=ax, linewidth=1.4)
    for _, row in provinces.iterrows():
        p = row.geometry.representative_point()
        ax.text(p.x, p.y, str(row.PROVINCE).upper(), fontsize=7, ha="center", va="center")
    ax.set_title("Tanganyika — Provinces and Districts, 1950")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(docs_dir / "Tanganyika_1950_preview.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
