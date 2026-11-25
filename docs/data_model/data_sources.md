# Data Sources

### Terrain

#### Dataset #1
- __Name__: USGS 3DEP 1m
- __Source__: https://apps.nationalmap.gov/downloader/
- __Notes__: USA only; bare-earth

### Weather

#### Dataset #2
- __Name__: National Weather Service API
- __Source__: https://www.weather.gov/documentation/services-web-api 
- __Notes__: Use interpolation for temperature, humidity, and wind speed/direction. Extra care needed for visibility & precipitation.

### Buildings

#### Dataset #3
- __Name__: FEMA USA Structures
- __Source__: https://gis-fema.hub.arcgis.com/pages/usa-structures
- __Direct Source__: https://gis-fema.hub.arcgis.com/pages/usa-structures-data
- __Notes__: Datasets downloadable as .gdb's by state. Largest ~2GB

### Aircraft

#### Dataset #4
- __Name__: Simulated UAS Data
- __Source__: Mock data module
- __Notes__: SITL Drone data, maybe use Gazebo

### Airspace Restriction

#### Dataset #5
- __Name__: FAA Special Use Airspace
- __Source__: https://adds-faa.opendata.arcgis.com/datasets/dd0d1b726e504137ab3c41b21835d05b_0/explore?location=39.152097%2C-77.219401%2C8 
- __Notes__: 

#### Dataset #6
- __Name__: FAA UAS Data Delivery
- __Source__: https://udds-faa.opendata.arcgis.com/
- __Direct Source__: https://udds-faa.opendata.arcgis.com/datasets/4254d2f81e5241cc8ba5883b63ae397c/explore?location=39.229163%2C-77.397848%2C10 
- __Notes__: This is actually several datasets, some of which I may not need now. Use FAA UAS Facility Map

### Controlled Airspace

#### Dataset #7
- __Name__: FAA NASR
- __Source__: https://www.faa.gov/air_traffic/flight_info/aeronav/Aero_Data/NASR_Subscription/ 
- __Notes__: Contains controlled airspace data; Zips posted once every 28 days, important data is stored as a csv.


