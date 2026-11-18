# Horizon v0.1 Ontology

### Introduction
Horzion v0.1 will feature a limited ontology. My plan is to expand Horizon's ontology gradually as development progresses and I gain domain knowledge.

### Core Entities
Horizon's ontology revolves around 7 core entities. Everything in a horizon world model either is a core entity or is related to a core entity. This list may change as Horizon evolves.

1) Aircraft
2) Airspace
3) Flight Procedure
4) Weather
5) Terrain
6) Facility
7) Spatial Feature

### v0.1 Limitations

Horzion v0.1 will only represent the following core entities:

1) Aircraft
2) Airspace
3) Weather
4) Terrain
5) Spatial Features

Flight procedures will not be represented as the FAA is still in the process of drafting the regulations governing beyond visual line of sight (BVLOS) drone operations. These regulations are expected to be finalized in early 2027 in a document called "Part 108". Recreational flight non-BVLOS commercial regulations defined "TRUST" and "Part 107" respectively. 

Facilities will not prerepresent as drones do not have robust infrastructure to interact with in the same way that traditional fixed wing aircraft do. Part of this is due to the fact that drones need less infrasture. Small UAVs can take off, land, recharge, and be stored just about anywhere. Boeing 737's require Airports. Another part of it is that the buildout of drone infrastructure is still in the early stages. As large commercial fleets become more common, I expect this category to become more relevant.

### Aircraft
Aircraft objects represent drones. One or more drones can belong to a swarm. Each drone has a flight path. Flight paths have waypoints. Each drone has telemetry.

#### Related Entities
- Drone
- Swarm
- Flight Path
- Flight Path Waypoint
- Telemetry

### Airspace
Airspace can have restrictions placed on it. Some restrictions are permanant, some are temporary. Airspace can be controlled. FAA regulations specify the meaning of different classes of controlled airspace.

#### Relevant Entities
- Controlled Airspace (Class A thru G)
- Restricted Airspace
- Temporary Flight Restriction (TFR)

### Terrain
Terrain is the ground.

#### Relevant Entities
- The Ground

### Weather
Weather is the atmospheric conditions that effect flight. Wind is an atmospheric condition. Precipitation is an atmospheric condition. Temperature is an atmospheric condition. Humidity is an atmospheric condition. Visibility is an atmospheric condition.

#### Relevant Entities
- Wind
- Precipitation
- Temperature
- Humidity
- Visibility

### Spatial Features
Spatial features are entities that have a GEOMETRY property and do not belong to any other core entity. Points, lines, polygons, and volumes are spatial entities. Waypoints and areas of interest are operational entities constructed from spatial features. Buildings and vegetation are surface features constructed from spatial features.

#### Relevant Entities
- Point
- Line
- Polygon
- Volume
- Waypoint
- Area of Interest
- Building
- Vegetation
