# Description of the input data

The input data has the following variables:
- All times are assumed to be in Finnish normal time, UTC+2
- The input data is in xlsx file and the number of data rows is assumed to be an integer multiple of 24
- `Te` is the outdoor air temperature at two meter height from the ground surface at the meteorological weather station, instantaneous value, degC
- `RHe_water` is the outdoor air relative humidity with respect to liquid water, measured at two meter height, instantaneous value, %
- `ws` is the wind speed at 10 m height, 15927-3:2009 terrain category II, instantaneous value, m/s
- `wd` is the wind direction at 10 m height, 15927-3:2009 terrain category II, instantaneous value, Deg (North = 0 Deg, East = 90 Deg, ...)
- `Rglob` is the global solar radiation measured at a horizontal surface, sum of direct and diffuse radiation, average value for the preceding hour, W/m2
- `Rdif` is the diffuse solar radiation measured at a horizontal surface, average value for the preceding hour, W/m2
- `Rbeam` is the solar radiation to a plane that is normal to the direction of the sun, average value for the preceding hour, W/m2
- `precip` is the total amount of rain to a horizontal surface, including both water and snow, average value for the preceding hour, dm3/(m2h)

The original data files were handled as follows:
1. The folder `originals` contains the .prn files that were downloaded from the [Finnish Meteorological Institute website](https://www.ilmatieteenlaitos.fi/rakennusfysiikan-ilmastolliset-testivuodet).
2. The header rows for the prn-files were replaced with the keywords described above and the files were renamed. These files are in the root of `input` folder.
3. The modified prn-files were read into Excel spreadsheet `bf_test_years_2020-04-20.xlsx` and the following changes were made:
    1. The building physical test year Jokioinen 2004 is originally a leap year (366 days), but the leap day (Feb 29th) was removed from the files to make all years 8760 hours long
    2. The original columns for index (t), year, month, day and hour were removed. All the test years have the first row as January 1st 00:00.
