# Geographic Market Intelligence — Eli Lilly Demo

End-to-end Databricks demo with three pieces:

| Folder | Contents |
| --- | --- |
| [`app/`](app) | Streamlit Databricks App (3 tabs: embedded dashboard, territory builder, territory viewer). See [`app/README.md`](app/README.md) for setup and deploy. |
| [`data_pipeline/`](data_pipeline) | Healthcare Claims Medallion pipeline notebook that produces the Bronze/Silver/Gold tables in `eli_lilly_demo`. |
| [`dashboard/`](dashboard) | Exported AI/BI dashboard definition (`.lvdash.json`) for the Population Health Executive Dashboard. |

Target workspace: <https://dbc-c294909e-40e9.cloud.databricks.com>
Deployed app: <https://geo-market-intel-7474656071514307.aws.databricksapps.com>
