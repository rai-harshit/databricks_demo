# genie_spaces/

Portable copy of the **Population Health Insights — Eli Lilly** Genie
Space: a natural-language chat interface over the same `eli_lilly_demo`
claims data the rest of the demo uses.

This directory is **optional** — the Streamlit app in `app/` does not
depend on it. Use it if you want to stand up the Genie experience in a
new workspace (or keep a versioned backup of the space).

## Contents

```
genie_space_export.json        Serialized space: tables, instructions,
                               example questions, benchmarks.
Import Export Genie Space.ipynb  Two-cell notebook — export an existing
                               space to JSON, import a JSON into a new
                               workspace.
```

## Import into a new workspace

1. Import `Import Export Genie Space.ipynb` into your workspace
   (Workspace → **Import** → upload the `.ipynb`).
2. Upload `genie_space_export.json` to a location your notebook can read
   (e.g. `/Workspace/Users/<you>/genie_space_export.json`).
3. Open the notebook, jump to the second cell (**Import Genie Space from
   JSON**), and set:
   - `IMPORT_FILE` → the workspace path from step 2.
   - `TARGET_WAREHOUSE_ID` → a warehouse in the target workspace.
4. Run the cell. It prints the new `space_id`; open it from **Genie →
   Spaces** in the Databricks UI.

The import assumes the referenced tables
(`eli_lilly_demo.gold_claims.*`, `eli_lilly_demo.silver_claims.*`) exist
and the caller has `USE CATALOG` / `SELECT` on them — run the
`data_pipeline/` notebook first, same as for the rest of the demo.

## Export a space (re-generate the JSON)

Open the first cell (**Export Genie Space to JSON**), replace `SPACE_ID`
with the space you want to snapshot and `OUTPUT_FILE` with where to
write it, then run it. Copy the resulting JSON back into this directory
to version-control the updated space definition.

## Troubleshooting

- `PERMISSION_DENIED` on the referenced tables → grant the caller (or
  the space's run-as identity) `USE CATALOG` on `eli_lilly_demo` and
  `SELECT` on the `gold_claims` / `silver_claims` schemas.
- `Warehouse not found` on import → `TARGET_WAREHOUSE_ID` must be a
  warehouse in the **target** workspace, not the source.
- Space imports but returns empty results → double-check the underlying
  tables exist; the serialized space pins table identifiers by name.
