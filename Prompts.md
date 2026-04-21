# Demo Guide

## Overview
This guide contains a series of prompts for demonstrating Databricks capabilities with healthcare claims data, including data engineering pipelines, Genie spaces, dashboards, and app development.

---

## Dataset Access
Get access to dataset in `healthverity_claims_sample_patient_dataset.hv_claims_sample` schema.

---

## Prompt Sequence

### Prompt #1: Create Medallion Architecture Pipeline

> I have a bunch of tables in healthverity_claims_sample_patient_dataset.hv_claims_sample schema. Explore the tables in this schema and then create a medallion architecture based data engineering pipeline. All of this should be in a new notebook. Consider healthverity_claims_sample_patient_dataset.hv_claims_sample as the raw schema. Create the silver and gold schemas under eli_lilly_demo catalog. Ask questions if you're not sure about something.

---

### Prompt #2: Create Genie Space

> Okay, look at the final gold tables you just created under eli_lilly_demo.gold_claims and eli_lilly_demo.silver_claims. Identify one theme for the Genie Space based on what you see in the data. Give me a bunch of options in terms of theme. Once I select the theme, create a Genie space and add those tables to that space.

---

### Prompt #3: Evaluate Genie Space Options

> Which of these will allow me to add maximum number of tables and really ask some wide variety of very interesting questions relevant to a company like Eli Lilly?

---

### Prompt #4: Build Genie Space with Sample Questions

> Perfect! Create a population health Genie space. Add the questions you proposed as sample questions to that space. Make sure all those questions do result in some output.

---

### Prompt #5: Create Insights Dashboard

> Now, can you also create a dashboard for me to show the most interesting insights across all the gold tables?

---

### Prompt #6: Generate App Development Prompt

> Now give me a detailed prompt mentioning all details like full table names, all table columns, and other such relevant details that I can use to build my Databricks app. Also add detailed instructions on what that app is supposed to do - show an integrated dashboard that you had created earlier, get inputs from the user, save it in a delta table (create if not exist), and then also fetch and show that input from other users. Be as detailed about the app as possible. Don't miss out any details. Don't give code snippets and give me only text.

---

## Notes
- Uses healthcare claims sample dataset from HealthVerity
- Target catalog: `eli_lilly_demo`
- Architecture: Medallion (Bronze → Silver → Gold)
- Processing: Batch only (no streaming)
