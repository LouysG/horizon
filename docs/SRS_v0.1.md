# Horizon v0.1 Software Requirements Specification

## 1. Introduction

### 1.1 Document Purpose

This document is the Software Requirements Specification (SRS) for Horizon Mk I. It defined the functional, data, interface, and non-functional requirements for Horizon Mk I.

### 1.2 System Overview

Horizon is a platform for creating digital twins of a drone's environment. The development of Horizon will proceed across multiple successive iterations of the Horizon platform. Each iteration will bear the suffix "Mark X" or "Mk X" to indicate its place in the sequence. 

Horizon Mk I is a real-time digital shadow of a drone's operating environment generated via the integration of multiple heterogeneous data sources.

The platform will ingest data data from multiple external sources, reconcile that data into a common representation, and use it to construct a world model. World models will provide a unified view of a geographically bounded area at a given point in time. They will contain entities such as aircraft, flight procedures, terrain, surface features, weather, and more. 

Horizon Mk I is intended to serve as a foundational data platform. The digital shadows it creates are meant to be consumed and manipulated by downstream applications such as UAS mission planners and flight control systems.

### 1.3 Users & External Systems
Horizon is intended to support software developers, UAS operators, and autonomous systems that require access to real-time structured geospatial information.

Horizon will interact with two categories of external systems:

1. __Data Providers__: Public and private sources supplying geographic, environmental, aviation, and other operationally relevant information.
2. __Data Consumers__: Applications and services that retrieve, query, or manipulate world models to support activities such as flight planning, simulation, and autonomous decision-making.

### 1.4 Operating Environment
Horizon will operate as a software platform situated between external geospatial data providers and downstream UAS applications. It will be responsible for acquiring, integrating, and exposing information about operating environments.

The platform must accommodate differences in source data formats, geographic coverage, update frequency, and completeness. Consequently, the availability and fidelity of individual world models will depend in part on the quality and coverage of the underlying datasets.

## 2. Functional Requirements
This section defines the functional capabilities required of Horizon v0.1. Requirements are organized by major system capability and describe the behaviors the platform must support.

### 2.1 Data Ingestion & Integration
Horizon shall support the acquisition and integration of heterogeneous geospatial datasets into a common representation.

- FR-001: The system shall support importing geospatial data from multiple external sources representing different categories of entities.

- FR-002: The system shall validate and transform imported data to conform to Horizon's common data model.

- FR-003: The system shall identify and report invalid records and ingestion failures.

### 2.2 World Model Generation
Horizon shall support the construction of geographically bounded world models representing UAS operating environments.

- FR-004: The system shall allow users to define the geographic extent and supported entity categories of a world model.

- FR-005: The system shall generate world models containing relevant entities and their relationships from integrated datasets.

### 2.3 World Model Interaction
Horizon shall provide mechanisms for querying, inspecting, and manipulating world models.

- FR-006: The system shall support querying world model entities by geographic location, entity category, and supported attributes.

- FR-007: The system shall allow users to inspect the attributes and relationships of individual entities.

- FR-008: The system shall support the creation, modification, and deletion of operator-defined features within world models.

### 2.4 World Model Visualization
Horizon shall provide basic geographic visualization capabilities for inspecting world models.

- FR-009: The system shall display world models and their constituent spatial entities in an interactive geographic visualization.

- FR-010: The system shall allow users to navigate the visualization and select entities for inspection.

## 3. Data Requirements
This section defines the information Horizon v0.1 must represent and the conditions governing its consistency, provenance, and persistence.

### 3.1 Core Data Model
Horizon shall maintain a common data model representing the entities and relationships relevant to UAS operating environments.

- DR-001: The data model shall support Horizon's eight core entity categories: Aircraft, Airspace, Flight Procedures, Terrain, Surface Features, Weather, Facilities, and Operational Features.

- DR-002: Entities shall have unique identifiers, defined attributes, and support relationships with other entities.

- DR-003: The data model shall accommodate missing or inapplicable attribute values without compromising data integrity.

### 3.2 Spatial & Temporal Data
Horizon shall support the representation of the spatial and temporal characteristics of operating environments.

- DR-004: The data model shall support spatial geometries, geographic coordinates, and elevation or altitude information appropriate to each entity type.

- DR-005: Spatial data shall use defined coordinate reference systems and consistent measurement units.

- DR-006: The data model shall support timestamps and temporal validity information for entities whose characteristics vary over time.

### 3.3 Data Provenance & Integrity
Horizon shall preserve the origins and consistency of integrated data.

- DR-007: Imported data shall retain sufficient provenance information to identify its originating source and acquisition time.

- DR-008: Stored data shall conform to the structural, semantic, and relational integrity constraints established by the common data model.

### 3.4 Data Persistence
Horizon shall maintain persistent representations of integrated data and world models.

- DR-009: Integrated datasets and generated world models shall remain available across application restarts.

- DR-010: The platform shall preserve the associations between world models and their constituent entities.

## 4. Interface Requirements
This section defines the interfaces through which Horizon v0.1 shall interact with external data sources, users, and other software. These requirements establish the forms of interaction the platform must support without prescribing their specific implementations.

### 4.1 Data Source Interfaces
Horizon shall provide interfaces for acquiring data from heterogeneous external sources.

- IR-001: The system shall support importing geospatial data from external files or datasets using documented, commonly supported formats.

- IR-002: The system shall accommodate differences in source data schemas, coordinate reference systems, and measurement units.

- IR-003: The system shall provide feedback on the outcome of data ingestion operations, including errors and rejected records.

### 4.2 User Interfaces
Horizon shall provide an interface through which users can generate, inspect, and interact with world models.

- IR-004: The system shall provide a user interface for defining geographic boundaries and generating world models.

- IR-005: The system shall provide an interactive geographic visualization of world models, including basic map navigation and entity inspection.

- IR-006: The system shall provide mechanisms for users to query world model contents and manage operator-defined operational features.

### 4.3 Programmatic Interfaces
Horizon shall expose its core capabilities through interfaces accessible to software components.

- IR-007: The system shall provide documented programmatic interfaces for generating, retrieving, and querying world models.

- IR-008: Programmatic interfaces shall use consistent, documented representations of entities, spatial data, and operation results.

- IR-009: Programmatic interfaces shall communicate invalid requests and operation failures through defined error responses.

## 5. Non-functional Requirements
This section defines the quality attributes and operational characteristics required of Horizon v0.1. These requirements establish expectations for system performance, reliability, maintainability, and portability appropriate to a standalone application.

### 5.1 Performance
Horizon shall provide acceptable performance when processing and interacting with geographically bounded world models on a single machine.

- NFR-001: The system shall provide sufficiently responsive interaction with generated world models to support routine exploration and inspection.

### 5.2 Reliability & Data Integrity
Horizon shall operate predictably and preserve the integrity of its stored data.

- NFR-002: The system shall handle invalid inputs and recoverable processing errors without unexpected termination or corruption of previously stored data.

- NFR-003: The system shall maintain data consistency across interrupted or failed data modification operations.

- NFR-004: The system shall be idempotent. I.e., produce consistent results when equivalent operations are performed against unchanged underlying data.

### 5.3 Maintainability & Testability
Horizon shall be structured to support incremental development, testing, and modification.

- NFR-005: The system shall maintain a separation of responsibilities between data ingestion, data management, world model generation, and presentation.

- NFR-006: The system shall provide automated tests covering its principal functional capabilities and data integrity constraints.

- NFR-007: The system shall provide sufficient diagnostic information to identify and investigate processing failures.

### 5.4 Portability & Reproducibility
Horizon shall support reproducible installation and execution in a local development environment.

- NFR-008: The system shall provide documented procedures for installing dependencies, configuring the application, and executing its principal operations.

- NFR-009: The system shall support reproducible execution on a documented, supported development environment without requiring externally hosted infrastructure.
