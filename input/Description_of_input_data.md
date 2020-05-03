# Description of the input data

The input data has the following variables:
- All times are in Finnish normal time, UTC+2
- `Te` is the outdoor air temperature at two meter height from the ground surface at the meteorological weather station, instantaneous value, degC
- `RHe_water` is the outdoor air relative humidity with respect to liquid water, measured at two meter height, instantaneous value, %
- `ws` is the wind speed at 10 m height, 15927-3:2009 terrain category II, instantaneous value, m/s
- `wd` is the wind direction at 10 m height, 15927-3:2009 terrain category II, instantaneous value, Deg (North = 0 Deg, East = 90 Deg, ...)
- `Rglob` is the global solar radiation measured at a horizontal surface, sum of direct and diffuse radiation, average value for the preceding hour, W/m2
- `Rdif` is the diffuse solar radiation measured at a horizontal surface, average value for the preceding hour, W/m2
- `Rbeam` is the solar radiation to a plane that is normal to the direction of the sun, average value for the preceding hour, W/m2
- `precip` is the total amount of rain to a horizontal surface, including both water and snow, average value for the preceding hour, dm3/(m2h)

