# Data Sources

### Terrain

#### Dataset #1
- __Name__: USGS 3DEP 1m
- __Source__: https://apps.nationalmap.gov/downloader/
- __Notes__: USA only; bare-earth

### Weather

#### Dataset #1
- __Name__: National Weather Service API
- __Source__: https://www.weather.gov/documentation/services-web-api 
- __Notes__: Use interpolation for temperature, humidity, and wind speed/direction. Extra care needed for visibility & precipitation.

#### Dataset #2
- __Name__: NOAA High-Resolution Rapid Refresh (HRRR)
- __Source__: https://rapidrefresh.noaa.gov/hrrr/
- __Notes__: Consider using for weather at altitude.

### Buildings

#### Dataset #1
- __Name__: FEMA USA Structures
- __Source__: https://gis-fema.hub.arcgis.com/pages/usa-structures
- __Notes__: Might not have smaller buildings.

### Aircraft

#### Dataset #1
- __Name__: Simulated UAS Data
- __Source__: Mock data module
- __Notes__: SITL Drone data, maybe use Gazebo

### Airspace Restriction

#### Dataset #1
- __Name__: FAA Special Use Airspace
- __Source__: https://adds-faa.opendata.arcgis.com/datasets/dd0d1b726e504137ab3c41b21835d05b_0/explore?location=39.152097%2C-77.219401%2C8 
- __Notes__:

#### Dataset #2
- __Name__: FAA UAS Data Delivery
- __Source__: https://udds-faa.opendata.arcgis.com/
- __Notes__: 

#### Dataset #3
- __Name__: FAA TFR List
- __Source__: https://tfr.faa.gov/tfr3/?page=list
- __Notes__:

### Controlled Airspace

#### Dataset #1
- __Name__: FAA NASR
- __Source__: https://www.faa.gov/air_traffic/flight_info/aeronav/Aero_Data/NASR_Subscription/ 
- __Notes__: Contains controlled airspace data.

