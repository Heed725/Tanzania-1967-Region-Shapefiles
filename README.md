# Tanzania Historical Region Shapefiles

Historical mainland Tanzania / Tanganyika administrative boundaries prepared for GIS use.

This repository now contains two historical boundary projects:

1. **Tanzania mainland regional reconstruction, 1967**
2. **Tanganyika provinces and districts, 1950**

---

# Tanzania 1967 Region Shapefiles

Reconstructed mainland Tanzania regional boundaries for **1967**, generated from the administrative boundary data in [`Heed725/Tanzania_Admin_Shapefiles`](https://github.com/Heed725/Tanzania_Admin_Shapefiles).

> **Important:** this is a historical reconstruction, not an official digitization of the original 1967 paper map. Modern district polygons are reassigned to their 1967 parent regions and dissolved. Small boundary differences can remain where district boundaries changed after 1967.

## 1967 mainland regions

The build validates that the final layer contains exactly these 17 regions:

1. Arusha
2. Coast
3. Dodoma
4. Iringa
5. Kigoma
6. Kilimanjaro
7. Mara
8. Mbeya
9. Morogoro
10. Mtwara
11. Mwanza
12. Ruvuma
13. Shinyanga
14. Singida
15. Tabora
16. Tanga
17. West Lake

## Reconstruction rules

The script reverses later administrative changes, including:

- Manyara → Arusha
- Dar es Salaam + Pwani → Coast
- Njombe → Iringa
- Songwe → Mbeya
- Rukwa → Mbeya
- Katavi → Tabora
- Lindi → Mtwara
- Kagera → West Lake
- Geita-area districts are split back between West Lake, Mwanza and Shinyanga according to their parent areas
- Simiyu is split back mainly to Shinyanga, while Busega returns to Mwanza because it was formed from Magu

The crosswalk used for every source polygon is exported as `data/district_to_1967.csv` by the workflow.

## 1967 outputs

```text
data/
├── Tanzania_Regions_1967.shp
├── Tanzania_Regions_1967.shx
├── Tanzania_Regions_1967.dbf
├── Tanzania_Regions_1967.prj
├── Tanzania_Regions_1967.cpg
├── Tanzania_Regions_1967.geojson
├── Tanzania_Regions_1967.gpkg
└── district_to_1967.csv

dist/
└── Tanzania_Regions_1967_Shapefile.zip

docs/
└── Tanzania_Regions_1967_preview.png
```

The workflow publishes/updates the GitHub Release **`1967-regions`**.

---

# Tanganyika Provinces and Districts — 1950

The Tanganyika dataset follows the historical administrative map shown in the colonial-era reference map: thick province boundaries with the internal district divisions preserved.

Unlike the 1967 layer, this is **not reconstructed from current Tanzania boundaries**. The workflow uses an existing historical GIS digitization from **Princeton University Library / Map and Geospatial Information Center**, distributed through the NYU Spatial Data Repository as **“Tanzania extracted historical administrative boundaries, 1950.”**

The source dataset represents historical **province and district polygons in Tanganyika** and was extracted from a scanned British Colonial Office / Tanganyika Department of Lands and Surveys map. The historical source map is documented as having administrative boundaries revised to **May 1950**.

Source catalogue:

- NYU Spatial Data Repository / Princeton: `Tanzania extracted historical administrative boundaries, 1950`
- Original historical mapping: Tanganyika Department of Lands & Surveys / British Colonial administration

## What the Tanganyika workflow creates

Two GIS layers are generated:

### Province layer

`Tanganyika_Provinces_1950`

District polygons are dissolved using the original historical `Province` attribute so that the heavy province boundaries can be mapped as in the reference image.

### District layer

`Tanganyika_Districts_1950`

The original historical district polygons are preserved and standardized for modern GIS software.

## Tanganyika 1950 outputs

```text
data/tanganyika_1950/
├── Tanganyika_Provinces_1950.shp
├── Tanganyika_Provinces_1950.shx
├── Tanganyika_Provinces_1950.dbf
├── Tanganyika_Provinces_1950.prj
├── Tanganyika_Provinces_1950.cpg
├── Tanganyika_Provinces_1950.geojson
├── Tanganyika_Provinces_1950.gpkg
│
├── Tanganyika_Districts_1950.shp
├── Tanganyika_Districts_1950.shx
├── Tanganyika_Districts_1950.dbf
├── Tanganyika_Districts_1950.prj
├── Tanganyika_Districts_1950.cpg
├── Tanganyika_Districts_1950.geojson
├── Tanganyika_Districts_1950.gpkg
│
├── Tanganyika_1950_Province_District_Crosswalk.csv
└── summary.json

dist/
├── Tanganyika_Provinces_1950_Shapefile.zip
└── Tanganyika_Districts_1950_Shapefile.zip

docs/
└── Tanganyika_1950_preview.png
```

The workflow publishes/updates the GitHub Release **`tanganyika-1950`**.

## Attribute fields

### Provinces

| Field | Meaning |
|---|---|
| `YEAR` | Historical reference year, 1950 |
| `TERRITORY` | Tanganyika |
| `PROVINCE` | Historical province name |

### Districts

| Field | Meaning |
|---|---|
| `YEAR` | Historical reference year, 1950 |
| `TERRITORY` | Tanganyika |
| `PROVINCE` | Historical parent province |
| `DISTRICT` | Historical district name |

## Coordinate reference system

The released GIS layers are standardized to:

```text
EPSG:4326
WGS 84
```

This makes them easy to combine with modern Tanzania datasets, Natural Earth, OpenStreetMap, QGIS, ArcGIS and web maps.

## Reproducing the colonial map appearance in QGIS

Load both Tanganyika layers and style them as follows:

1. Put `Tanganyika_Districts_1950` underneath.
2. Give district boundaries a thin line.
3. Put `Tanganyika_Provinces_1950` above the districts.
4. Set the province polygon fill to transparent.
5. Give the province outline a much thicker line.
6. Label provinces using `PROVINCE`.
7. Label districts using `DISTRICT` at a smaller font size.
8. Add rivers, lakes, railways and roads separately if you want to recreate the full historical sheet appearance.

The automatically generated `docs/Tanganyika_1950_preview.png` uses this same visual hierarchy: thin district boundaries and heavier province boundaries.

## Tanganyika automation

`.github/workflows/build-tanganyika-1950.yml` automatically:

1. downloads the Princeton historical Tanganyika boundary dataset;
2. extracts the historical shapefile;
3. keeps the original Province and District attributes;
4. validates and repairs geometries;
5. converts the data to EPSG:4326;
6. generates province and district Shapefiles;
7. generates GeoJSON and GeoPackage versions;
8. creates a province–district CSV crosswalk;
9. renders a preview map;
10. packages the Shapefiles as ZIP files;
11. commits generated GIS files back to the repository; and
12. publishes them to the `tanganyika-1950` GitHub Release.

---

# Using the data in QGIS

For either historical dataset:

1. Open the repository **Releases** page.
2. Choose `1967-regions` or `tanganyika-1950`.
3. Download the required Shapefile ZIP.
4. Extract it.
5. Open QGIS.
6. Select **Layer → Add Layer → Add Vector Layer**.
7. Select the `.shp` file.
8. Click **Add**.

You can also use the `.gpkg` file directly; GeoPackage is generally easier to manage than a multi-file Shapefile.

# Python / GeoPandas example

```python
import geopandas as gpd

provinces = gpd.read_file(
    "data/tanganyika_1950/Tanganyika_Provinces_1950.gpkg"
)

print(provinces[["PROVINCE"]])
provinces.plot()
```

# R / sf example

```r
library(sf)

provinces <- st_read(
  "data/tanganyika_1950/Tanganyika_Provinces_1950.gpkg"
)

plot(provinces["PROVINCE"])
```

# Historical-data note

Historical boundaries should not automatically be treated as equivalent to current administrative boundaries. Province and district names, jurisdictions and boundary locations changed repeatedly during the colonial and post-independence periods.

For the Tanganyika 1950 dataset, the historical digitization is preferable to approximating colonial boundaries by dissolving present-day Tanzania regions.
