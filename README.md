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

## Outputs

After the GitHub Actions build completes, the repository contains:

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

The workflow also publishes/updates a GitHub Release named **1967-regions** with the ZIP shapefile package, GeoJSON and GeoPackage.

## QGIS

Download `Tanzania_Regions_1967_Shapefile.zip`, extract it, then open `Tanzania_Regions_1967.shp` in QGIS.

The output is converted to **EPSG:4326 (WGS 84)**.

## Rebuild locally

```bash
python -m pip install -r requirements.txt
python scripts/build_1967_regions.py --source ../Tanzania_Admin_Shapefiles
```

## Automation

`.github/workflows/build-1967-regions.yml` checks out the source repository, rebuilds the historical layer, validates the 17-region result, commits generated files, and refreshes the downloadable release assets.

## Historical basis

The reconstruction follows the 17-region mainland arrangement used in the 1960s: Arusha, Coast, Dodoma, Iringa, Kigoma, Kilimanjaro, Mara, Mbeya, Morogoro, Mtwara, Mwanza, Ruvuma, Shinyanga, Singida, Tabora, Tanga and West Lake. Later regions are reversed to their parent regions using documented administrative histories.
