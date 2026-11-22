# Ingestion Module Design Doc
In general, the ingestion module is an on-demand batch importer that gathers the data necessary to build a spatially and temporally bounded world model.

## Ingestion Process

### Stages
- Plan
- Acquire
- Transform
- Persist

### Plan
The "Plan" stage takes an area of interest and a time interval, and identifies which datasets, what versions of those datasets, and what subset of that particular version must be pulled to construct the desired world model.

### Acquire
The "Acquire" stage downloads the datasets identified in the previous step.

Metadata such as data source, version, acquisition time, and so on are recorded.

If a copy of the data already exists in the database, that is used instead.

### Transform
Data is transformed from the source schema to Horizon's schema.

### Persist
Persist the transformed data in the database
