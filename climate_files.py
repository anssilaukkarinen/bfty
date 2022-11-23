# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 11:16:35 2020
Author: Anssi Laukkarinen, anssi.laukkarinen@tuni.fi

For the current status of code and license information, see:
https://github.com/anssilaukkarinen/bfty

"""

import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt


Rw = 461.5
Te_min = -30.0 # WDR

Pe_basevalue = 101325.0


# Height of building from ground surface to roof top, m
h = 6.0
print('h', h)

# Direction of the facade being analysed: 0 deg = north, 90 deg = east
orientation = 180.0
print('orientation:', orientation)

# Terran category, where the building is located
# The classes are the same in SFS-EN 1991-1-4 and SFS-EN ISO 15927-3
terrain_category = 'I'
print('terrain_category:', terrain_category)

# Topography coefficient, C_T = 1.0 for flat country
C_T = 1.0
print('C_T:', C_T)

# Obstruction factor for wind-driven rain
O = 0.8
print('O:', O)

# Wall factor for wind-driven rain
W = 0.4
print('W:', W)

lwidth = 0.6







# Averaging time for indoor air relative humidity
window_width = 24


def pvsat_water(T):
    # CIMO guide
    pvsat = 611.2*np.exp((17.62*T)/(243.12+T))
    return(pvsat)

def pvsat_ice(T):
    # CIMO guide
    pvsat = np.empty(T.shape)
    for idx,val in enumerate(T):
        if val < 0:
            pvsat[idx] = 611.2*np.exp(22.46*val/(272.62+val))
        else:
            pvsat[idx] = 611.2*np.exp(17.62*val/(243.12+val))
    return(pvsat)
    

def dv(Te):
    # Finnish Association of Civil Engineers, guidebook 107-2012
    # Moisture class 2
    xp = (-30,5,15,30)
    fp = (0.005,0.005,0.002,0.002)
    vals = np.interp(Te,xp,fp)
    return(vals)

def T_S2(Te):
    # Finnish indoor classification, class S2
    xp = (-30, 0, 20, 30)
    fp = (21.5, 21.5, 25.5, 25.5)
    vals = np.interp(Te, xp, fp)
    return(vals)


def get_smallest_angle(source_angle_deg, target_angle_deg):
    # Calculate the smalles difference between two angles
    # e.g. 90 deg, not 270 deg
    # https://stackoverflow.com/questions/1878907/the-smallest-difference-between-2-angles
    
    a = target_angle_deg -  source_angle_deg
    
    if a > 180.0:
        a -= 360.0
        
    elif a < -180.0:
        a += 360.0
    
    return(a)



def get_cpe1(wd, orientation):
    # SFS-EN 1991-1-4, Moisio et al 2019
    
    cpe1 = np.zeros(len(wd))
        
    
    for idx, wd_val in enumerate(wd):
        a_deg = get_smallest_angle(wd_val, orientation)
        a_deg = np.abs(a_deg)
        
        if a_deg >= 135.0:
            # Wind is blowing from the opposite side of the building
            cpe1[idx] = -0.5
        elif a_deg < 45.0:
            # Wind is blowing towards the facade
            cpe1[idx] = +1.0
        else:
            # Wind is blowing from the side
            cpe1[idx] = -1.4
        
    
    return(cpe1)
    


def calc_dP(Te, Ti, Pe, ws_local, wd_local, h, orientation):
    """
    Te outdoor air temperature, degC
    Ti indoor air temperature, degC
    Pe air pressure in the outdoor air, Pa   
    ws_local wind speed at the building site, m/s
    wd_local wind direction at the building site, 0 = north, 90 = east
    h building height from ground surface to top of roof, m
    orientation of the facade, 0 = north, 90 = east-facing wall
    """
    g = 9.81
    Ra = 287.0
    
    # z vertical distance from air pressure neutral axis to point of interest, m
    z = h/2.0
    
    ## Air pressure difference from temperature differences    
    dPT = (g*z*Pe/Ra) * (1/(273.15+Te) - 1/(273.15+Ti))
    
    
    ## Air pressure difference from wind
    # Average air density, constant pressure of 101325 Pa is assumed
    Tave = (Te + Ti) / 2
    rhoa = 101325.0 / (Ra * (273.15 + Tave))
    
    cpe = get_cpe1(wd_local, orientation)
    
    use_recommendation = False
    if use_recommendation:
        cpi = -0.3
    else:
        cpi = np.zeros(cpe.shape)
        for idx, val in enumerate(cpe):
            if val > 0.0:
                cpi[idx] = -0.3
            else:
                cpi[idx] = 0.2
                
    
    dPw = (cpi - cpe) * (0.5*rhoa*ws_local**2)
    
    
    ## Total
    dP = dPT + dPw
    return(dPT, dPw, dP)
    #return(dP)


def get_c_r(z, terrain_category='II', method='ISO_15927_3'):
    # SFS-EN ISO  roughness coefficient
    # Parameter z is the building height from ground surface to roof top, m
    
    if method == 'ISO_15927_3':
        if terrain_category == 'I':
            K_R = 0.17
            z_0 = 0.01
            z_min = 2.0
        elif terrain_category == 'II':
            K_R = 0.19
            z_0 = 0.05
            z_min = 4.0
        elif terrain_category == 'III':
            K_R = 0.22
            z_0 = 0.3
            z_min = 8.0
        elif terrain_category == 'IV':
            K_R = 0.24
            z_0 = 1.0
            z_min = 16.0
        else:
            print('Error in terrain category!')
            z_min = np.nan
            z_0 = np.nan
        
        z_calc = np.maximum(z, z_min)
        c_R = K_R * np.log(z_calc/z_0)
    
    
    elif method == 'ISO_1991_1_4':
        if terrain_category == 'I':
            z_0 = 0.01
            z_min = 1.0
        elif terrain_category == 'II':
            z_0 = 0.05
            z_min = 2.0
        elif terrain_category == 'III':
            z_0 = 0.3
            z_min = 5.0
        elif terrain_category == 'IV':
            z_0 = 1.0
            z_min = 10.0
        else:
            print('Error in terrain category!')
            z_min = np.nan
            z_0 = np.nan
        
        z_calc = np.maximum(z, z_min)
        z_0II = 0.05
        kr = 0.19 * (z_0/z_0II)**0.07
        c_R = kr * np.log(z_calc/z_0)
        
    return(c_R)


def calculate_I_A(ws, wd, precip, Te, Te_min, wall_orientation):
    # Airfield spell index
    # This is the amount of free-flow driving rain in weather station conditions    
    # The local wind speed at building site is ws_airfield * C_R
    
    I_A = np.zeros(ws.shape)
    
    for idx, val in enumerate(ws):
        
        d_rad = get_smallest_angle(wall_orientation, wd[idx]) * (np.pi/180)
        cosine_term = np.maximum(np.cos(d_rad), 0.0)
        
        if Te[idx] >= Te_min:
            precip_val = precip[idx]
        else:
            precip_val = 0.0
                
        I_A[idx] = (2/9) * ws[idx] * precip_val**(8/9) * cosine_term
        
    return(I_A)
    










col_names = ['Te', 'RHe_water', 'RHe_ice', \
             'Ti_21', 'RHi_Ti21', \
             'Ti_S2', 'RHi_TiS2', \
             'ws', 'wd', 'precip', \
             'Rdif', 'Rdir', 'Rbeam', \
             'LWdn', \
             'Pe',
             'Pi',
             'WDR']

D5_keywords = ['TEMPER C', 'RELHUM %', 'RELHUM %', \
               'TEMPER C', 'RELHUM %', \
               'TEMPER C', 'RELHUM %', \
               'WINDVEL m/s', 'WINDDIR Deg', 'HORRAIN l/m2h', \
               'DIFRAD W/m2', 'DIRRAD W/m2', \
               'SKYEMISS W/m2', \
               'GASPRESS Pa',
               'GASPRESS Pa',
               'ThisIsPlaceHolderForWDR l/m2s']

D6_names = ['Temperature C', 'RelativeHumidity %', 'RelativeHumidity %', \
            'Temperature C', 'RelativeHumidity %', \
            'Temperature C', 'RelativeHumidity %', \
            'WindVelocity m/s', 'WindDirection Deg', 'RainFluxHorizontal l/m2h', \
            'SWRadiationDiffuse W/m2', 'SWRadiationDirect W/m2', 'DirectRadiationNormal W/m2', \
            'LWRadiationSkyEmission W/m2', \
            'GasPressure Pa',
            'GasPressure Pa',
            'RainFluxNormal l/m2s']

test_year_names = ['Jokioinen 2004', 'Jokioinen 2030', \
                   'Jokioinen 2050', 'Jokioinen 2100', \
                   'Vantaa 2007', 'Vantaa 2030', \
                   'Vantaa 2050', 'Vantaa 2100']


WUFI_wac_headers_outdoor_jok = ['WUFI®_WAC_02', \
                             "10	Line Offset to 'Number of Data Columns'", \
                             '', \
                             'A Finnish Building physical test year', \
                             '23.50	Longitude [°]; East is positive', \
                             "60.81	Latitude [°]; North is positive", \
                             '104	HeightAMSL [m]', \
                             '2.0	Time Zone [h from UTC]; East is positive', \
                             '1	Time Step [h]', \
                             '8760	Number of DataLines', 
                             '9	Number of DataColumns', \
                             'TA HREL ISDH ISD ILAH RN WD WS PMSL']

WUFI_wac_headers_outdoor_van = ['WUFI®_WAC_02', \
                             "10	Line Offset to 'Number of Data Columns'", \
                             '', \
                             'A Finnish Building physical test year', \
                             '24.96	Longitude [°]; East is positive', \
                             "60.33	Latitude [°]; North is positive", \
                             '51	HeightAMSL [m]', \
                             '2.0	Time Zone [h from UTC]; East is positive', \
                             '1	Time Step [h]', \
                             '8760	Number of DataLines', 
                             '9	Number of DataColumns', \
                             'TA HREL ISDH ISD ILAH RN WD WS PMSL']




WUFI_wac_headers_indoor_jok = ['WUFI®_WAC_02', \
                             "10	Line Offset to 'Number of Data Columns'", \
                             '', \
                             'Indoor air conditions for a Finnish Building physical test year', \
                             '23.50	Longitude [°]; East is positive', \
                             "60.81	Latitude [°]; North is positive", \
                             '104	HeightAMSL [m]', \
                             '2.0	Time Zone [h from UTC]; East is positive', \
                             '1	Time Step [h]', \
                             '8760	Number of DataLines', 
                             '3	Number of DataColumns', \
                             'TA HREL PMSL']


WUFI_wac_headers_indoor_van = ['WUFI®_WAC_02', \
                             "10	Line Offset to 'Number of Data Columns'", \
                             '', \
                             'Indoor air conditions for a Finnish Building physical test year', \
                             '24.96	Longitude [°]; East is positive', \
                             "60.33	Latitude [°]; North is positive", \
                             '51	HeightAMSL [m]', \
                             '2.0	Time Zone [h from UTC]; East is positive', \
                             '1	Time Step [h]', \
                             '8760	Number of DataLines', 
                             '3	Number of DataColumns', \
                             'TA HREL PMSL']




# Read
data = pd.read_excel('./input/bf_test_years_2020-04-20.xlsx', \
                     sheet_name=None)


# Calculate and write files
print('Current variables are:', data.keys())

for idx_year, year in enumerate(data.keys()):
    
    print('year:', year)
    
    # LWdn
    fname = './LWrad/'+year + '_LWdn_emissivity_Tsky_dTsky.csv'
    data[year]['LWdn'] = pd.read_csv(fname, sep='\s+', \
                                   usecols=[0], skiprows=0)
    
    
    # Rdir
    data[year]['Rdir'] = data[year]['Rglob'].values - data[year]['Rdif'].values
    
    # Indoor air, Ti = constant 21 degC, hourly
    Te = data[year].loc[:,'Te']
    RHe_water = data[year].loc[:,'RHe_water']
    ve = (RHe_water/100.0)*pvsat_water(Te) / (Rw*(273.15+Te))
    
    Ti_21 = 21.0 * np.ones(8760)
    Te_rolling_mean = Te.rolling(window_width, min_periods = 1).mean()
    ve_rolling_mean = ve.rolling(window_width, min_periods = 1).mean()
    vi_Ti21 = ve_rolling_mean + dv(Te_rolling_mean)
    vsat_Ti21 = pvsat_water(Ti_21)/(Rw*(273.15+Ti_21))
    RHi_Ti21 = np.minimum(95.0, 100.0 * vi_Ti21 / vsat_Ti21)
    
    data[year]['Ti_21'] = Ti_21
    data[year]['vi_Ti21'] = vi_Ti21
    data[year]['RHi_Ti21'] = RHi_Ti21
    
    
    # Indoor air, Ti ~ S2, daily
    Ti_S2 = T_S2(Te_rolling_mean)
    vi_TiS2 = vi_Ti21.copy()
    vsat_TiS2 = pvsat_water(Ti_S2)/(Rw*(273.15+Ti_S2))
    RHi_TiS2 = np.minimum(95.0, 100.0 * vi_TiS2 / vsat_TiS2)
    
    data[year]['Ti_S2'] = Ti_S2
    data[year]['vi_TiS2'] = vi_TiS2
    data[year]['RHi_TiS2'] = RHi_TiS2
    
    
    # Outdoor air relative humidity with respect to ice
    RHe_ice = np.minimum(100.0, RHe_water * (pvsat_water(Te)/pvsat_ice(Te)))
    data[year].loc[:,'RHe_ice'] = RHe_ice
    
    
    
    # Pe
    data[year]['Pe'] = 101325.0 * np.ones(8760)
    
    
    # Pi, SFS-EN 1991-1-4
    C_R = get_c_r(h, terrain_category, method='ISO_1991_1_4')
    print('C_R, pressure difference:', C_R)
    data[year]['ws_local'] = data[year].loc[:,'ws'] * C_R * C_T
    
    varname_Pi = 'Pi_' + terrain_category + '_' \
            + str(h) + 'm_' \
            + str(orientation) + 'deg'
            
    dPT, dPw, dP = calc_dP(data[year].loc[:,'Te'], 
                     data[year]['Ti_S2'], 
                     data[year]['Pe'], 
                     data[year].loc[:,'ws_local'], 
                     data[year].loc[:,'wd'], 
                     h, orientation)
    data[year][varname_Pi+'_dPT'] = dPT
    data[year][varname_Pi+'_dPw'] = dPw
    data[year][varname_Pi+'_dP'] = dP
    data[year][varname_Pi] = data[year]['Pe'] + dP
    
    


    # WDR, SFS-EN ISO 15927-3
    # x1 = data[year].loc[1:, 'precip'].values
    # x2 = data[year].loc[0, 'precip']
    # precip = np.append(x1, x2)
    
    # I_A can be handled as instantaneous values from here onwards
    I_A = calculate_I_A(data[year].loc[:,'ws'], 
                        data[year].loc[:,'wd'], 
                        data[year].loc[:, 'precip'], 
                        data[year].loc[:,'Te'], 
                        Te_min,
                        orientation)
    
    C_R = get_c_r(h, terrain_category, method='ISO_15927_3')
    print('C_R_WDR:', C_R)
    
    varname_WDR = 'WDR_' + terrain_category + '_' \
                    + str(h) + 'm_' \
                    + str(orientation) + 'deg'
    
    # These are considered as instantaneous/following-hour values
    # They are changed to preciding hour values
    # Delphin 6 (at least earlier version) required unit to be: l/(m2s)
    dummy = I_A * C_R * C_T * O * W / 3600
    print('RainFluxNormal vuodessa', year, 'l/(m2a):', np.sum(dummy*3600))
    # x1 = dummy[-1]
    # x2 = dummy[0:-1]
    # data[year][varname_WDR] = np.append(x1, x2)
    data[year][varname_WDR] = dummy
    

    
    
    
    
    ## Plot figures
    if not os.path.exists('./output/figures/'+year):
        os.makedirs('./output/figures/'+year)
    
    lwidth = 0.6
    
    # Te
    key = 'Te'
    plt.figure()
    plt.plot(data[year].loc[:,key].values, linewidth=lwidth)
    plt.grid()
    plt.xlabel('Aika vuoden alusta, h')
    plt.ylabel(key)
    plt.ylim((-30, 35))
    plt.title(year)
    fname = './output/figures/' + year + '/' + key + '.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight')
    plt.close()
    
    # RHe_water
    key = 'RHe_water'
    plt.figure()
    plt.plot(data[year].loc[:,key].values, linewidth=lwidth)
    plt.grid()
    plt.xlabel('Aika vuoden alusta, h')
    plt.ylabel(key)
    plt.ylim((-3, 103))
    plt.title(year)
    fname = './output/figures/' + year + '/' + key + '.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight')
    plt.close()
    
    # RHe_ice
    key = 'RHe_ice'
    plt.figure()
    plt.plot(data[year].loc[:,key].values, linewidth=lwidth)
    plt.grid()
    plt.xlabel('Aika vuoden alusta, h')
    plt.ylabel(key)
    plt.ylim((-3, 103))
    plt.title(year)
    fname = './output/figures/' + year + '/' + key + '.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight')
    plt.close()
    
    
    # Ti = 21
    key = 'Ti_21'
    plt.figure()
    plt.plot(data[year].loc[:,key].values, linewidth=lwidth)
    plt.grid()
    plt.xlabel('Aika vuoden alusta, h')
    plt.ylabel(key)
    plt.ylim((15, 30))
    plt.title(year)
    fname = './output/figures/' + year + '/' + key + '.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight')
    plt.close()
    
    # Ti ~ S2
    key = 'Ti_S2'
    plt.figure()
    plt.plot(data[year].loc[:,key].values, linewidth=lwidth)
    plt.grid()
    plt.xlabel('Aika vuoden alusta, h')
    plt.ylabel(key)
    plt.ylim((15, 30))
    plt.title(year)
    fname = './output/figures/' + year + '/' + key + '.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight')
    plt.close()
    
    # RHi_Ti21
    key = 'RHi_Ti21'
    plt.figure()
    plt.plot(data[year].loc[:,key].values, linewidth=lwidth)
    plt.grid()
    plt.xlabel('Aika vuoden alusta, h')
    plt.ylabel(key)
    plt.ylim((-3, 103))
    plt.title(year)
    fname = './output/figures/' + year + '/' + key + '.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight')
    plt.close()
    
    # RHi_TiS2
    key = 'RHi_TiS2'
    plt.figure()
    plt.plot(data[year].loc[:,key].values, linewidth=lwidth)
    plt.grid()
    plt.xlabel('Aika vuoden alusta, h')
    plt.ylabel(key)
    plt.ylim((-3, 103))
    plt.title(year)
    fname = './output/figures/' + year + '/' + key + '.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight')
    plt.close()
    
    
    
    # dP
    dP = data[year][varname_Pi] - data[year]['Pe']
    plt.figure()
    plt.plot(dP, linewidth=lwidth)
    plt.grid()
    plt.title(year)
    plt.xlabel('Aika vuoden alusta, h')
    plt.ylabel('dP, Pa')
    fname = './output/figures/' + year + '/' + 'dP' + '.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight')
    
    
    
    # Wind-driven rain
    wdr_cumsum = data[year].loc[:,varname_WDR].cumsum().values*3600
    plt.figure()
    plt.plot(wdr_cumsum, linewidth=lwidth)
    plt.grid()
    plt.title(year)
    plt.xlabel('Aika vuoden alusta, h')
    plt.ylabel('WDR kumulatiivinen, kg/m2')
    fname = './output/figures/' + year + '/' + varname_WDR + '_cumulative.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight')
    
    
    
    
    ## Export to csv files
    # precip, Rdif, Rdir, Rbeam and LWdn are average values for the preceding
    # hour. If needed, they can be changed to correspond to the following hour.
    move_cumulative_to_following = False
    
    if not os.path.exists('./output/csv/'+year):
        os.makedirs('./output/csv/'+year)
    
    for idx, col_name in enumerate(col_names):
        
        if col_name == 'Pi':
            col_name = varname_Pi
        elif col_name == 'WDR':
            col_name = varname_WDR
        
        fname = './output/csv/'+year+'/'+col_name+'.csv'
        
        if move_cumulative_to_following:
            if col_name in ['precip', 'Rdif', 'Rdir', 'Rbeam', 'LWdn', varname_WDR]:
                # Move one hour earlier
                x1 = data[year].loc[1:,col_name].values
                x2 = data[year].loc[0,col_name]
                x = np.append(x1,x2)
            else:
                x = data[year].loc[:,col_name].values
        
        else:
            x = data[year].loc[:,col_name].values
        
        X = np.column_stack((np.arange(len(x)), x))
        
        if col_name == varname_WDR:
            number_format = '%.2e'
        else:
            number_format = '%.2f'
        
        np.savetxt(fname, X, fmt=('%-2d', number_format), \
                   header='t    '+D6_names[idx], \
                   comments='')
    
    

    ## Export to Delphin 5 files
    if not os.path.exists('./output/Delphin5/'+year):
        os.makedirs('./output/Delphin5/'+year)
    
    dummy = [x for x in col_names if x not in ['Rbeam']]
    
    for idx, col_name in enumerate(dummy):
        
        if col_name == 'Pi':
            col_name = varname_Pi
        elif col_name == 'WDR':
            col_name = varname_WDR
        
        fname = './output/Delphin5/'+year+'/'+col_name+'.ccd'
        
        with open(fname, 'w') as f:
            
            # Header
            linetowrite = D5_keywords[idx]
            f.write(linetowrite + '\n')
            
            # Data rows
            if col_name in ['precip', 'Rdif', 'Rdir', 'Rbeam', 'LWdn', varname_WDR]:
                # The input data files has these as for the preciding hour,
                # but Delphin uses the values for future time steps.
                x1 = data[year].loc[1:,col_name]
                x2 = data[year].loc[0,col_name]
                x = np.append(x1,x2)
            else:
                x = data[year].loc[:,col_name]
            
            for t in range(8760):
                hour = t % 24
                day = int((t-hour)/24)
                val = x[t]
                
                if col_name == varname_WDR:
                    linetowrite = '{:<4d} {:02d}:00:00 {:.2e}'.format(day, hour, val)
                else:
                    linetowrite = '{:<4d} {:02d}:00:00 {:.2f}'.format(day, hour, val)
                
                f.writelines(linetowrite + '\n')
    
    
    
    ## Export to Delphin 6 files
    # The values correspond to instantaneous values and for integrals of
    # the preceding hour
    if not os.path.exists('./output/Delphin6/'+year):
        os.makedirs('./output/Delphin6/'+year)
    
    for idx, col_name in enumerate(col_names):
        
        if col_name == 'Pi':
            col_name = varname_Pi
        elif col_name == 'WDR':
            col_name = varname_WDR
        
        fname = './output/Delphin6/'+year+'/'+col_name+'.ccd'
        
        with open(fname, 'w') as f:
            
            # Header
            linetowrite = D6_names[idx]
            f.write(linetowrite + '\n')
            
            # Data rows
            # if col_name in ['precip', 'Rdif', 'Rdir', 'Rbeam', 'LWdn']:
            #     x1 = data[year].loc[1:,col_name]
            #     x2 = data[year].loc[0,col_name]
            #     x = np.append(x1,x2)
            # else:
            x = data[year].loc[:,col_name]
                        
            for t in range(8760):
                hour = t % 24
                day = int((t-hour)/24)
                val = x[t]
                
                if col_name == varname_WDR:
                    linetowrite = '{:<4d} {:02d}:00:00 {:.2e}'.format(day, hour, val)
                else:
                    linetowrite = '{:<4d} {:02d}:00:00 {:.2f}'.format(day, hour, val)
                
                f.write(linetowrite + '\n')
                
                
    ## Export outdoor data to WUFI files, RHe over water
    # Hourly data in WUFI is given for the preciding hour
    x1 = data[year].loc[1:,'Te']
    x2 = data[year].loc[0,'Te']
    TA = np.append(x1, x2)
    x1 = data[year].loc[1:,'RHe_water']
    x2 = data[year].loc[0,'RHe_water']
    HREL = np.append(x1, x2) / 100.0
    ISDH = data[year].loc[:,'Rdir']
    ISD = data[year].loc[:,'Rdif']
    ILAH = data[year].loc[:,'LWdn']
    RN = data[year].loc[:,'precip']
    x1 = data[year].loc[1:,'wd']
    x2 = data[year].loc[0,'wd']
    WD = np.append(x1,x2)
    x1 = data[year].loc[1:,'ws']
    x2 = data[year].loc[0,'ws']
    WS = np.append(x1,x2)
    PMSL = data[year].loc[:,'Pe'] / 100.0    
    
    
    if not os.path.exists('./output/WUFI/outdoor_over_water'):
        os.makedirs('./output/WUFI/outdoor_over_water')
    
    fname = './output/WUFI/outdoor_over_water/' + year + '_RHe_water.wac'
    
    with open(fname, mode='w', encoding='ANSI') as f:
        if 'jok' in year:
            f.writelines(WUFI_wac_headers_outdoor_jok[0] + '\n')
            f.writelines(WUFI_wac_headers_outdoor_jok[1] + '\n')
            f.writelines(WUFI_wac_headers_outdoor_jok[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,11):
                f.writelines(WUFI_wac_headers_outdoor_jok[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_outdoor_jok[-1].split(' ')) + '\n')
            
        elif 'van' in year:
            f.writelines(WUFI_wac_headers_outdoor_van[0] + '\n')
            f.writelines(WUFI_wac_headers_outdoor_van[1] + '\n')
            f.writelines(WUFI_wac_headers_outdoor_van[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,11):
                f.writelines(WUFI_wac_headers_outdoor_van[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_outdoor_van[-1].split(' ')) + '\n')

        for t in range(8760):
            txt = '{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}'
            vals = [TA[t], HREL[t], ISDH[t], ISD[t], ILAH[t], RN[t], WD[t], WS[t], PMSL[t]]
            linetowrite = txt.format(*vals)
            f.write(linetowrite + '\n')
            
            

    ## Export outdoor data to WUFI files, RHe over ice
    x1 = data[year].loc[1:,'Te']
    x2 = data[year].loc[0,'Te']
    TA = np.append(x1, x2)
    x1 = data[year].loc[1:,'RHe_ice']
    x2 = data[year].loc[0,'RHe_ice']
    HREL = np.append(x1, x2) / 100.0
    ISDH = data[year].loc[:,'Rdir']
    ISD = data[year].loc[:,'Rdif']
    ILAH = data[year].loc[:,'LWdn']
    RN = data[year].loc[:,'precip']
    x1 = data[year].loc[1:,'wd']
    x2 = data[year].loc[0,'wd']
    WD = np.append(x1,x2)
    x1 = data[year].loc[1:,'ws']
    x2 = data[year].loc[0,'ws']
    WS = np.append(x1,x2)
    PMSL = data[year].loc[:,'Pe'] / 100.0    
    
    
    if not os.path.exists('./output/WUFI/outdoor_over_ice'):
        os.makedirs('./output/WUFI/outdoor_over_ice')
    
    fname = './output/WUFI/outdoor_over_ice/' + year + '_RHe_ice.wac'
    
    with open(fname, mode='w', encoding='ANSI') as f:
        if 'jok' in year:
            f.writelines(WUFI_wac_headers_outdoor_jok[0] + '\n')
            f.writelines(WUFI_wac_headers_outdoor_jok[1] + '\n')
            f.writelines(WUFI_wac_headers_outdoor_jok[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,11):
                f.writelines(WUFI_wac_headers_outdoor_jok[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_outdoor_jok[-1].split(' ')) + '\n')
            
        elif 'van' in year:
            f.writelines(WUFI_wac_headers_outdoor_van[0] + '\n')
            f.writelines(WUFI_wac_headers_outdoor_van[1] + '\n')
            f.writelines(WUFI_wac_headers_outdoor_van[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,11):
                f.writelines(WUFI_wac_headers_outdoor_van[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_outdoor_van[-1].split(' ')) + '\n')

        for t in range(8760):
            txt = '{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}'
            vals = [TA[t], HREL[t], ISDH[t], ISD[t], ILAH[t], RN[t], WD[t], WS[t], PMSL[t]]
            linetowrite = txt.format(*vals)
            f.write(linetowrite + '\n')
    
    
    # Export indoor data to WUFI files, Ti = 21 degC
    x1 = data[year].loc[1:,'Ti_21']
    x2 = data[year].loc[0,'Ti_21']
    TA = np.append(x1, x2)
    x1 = data[year].loc[1:,'RHi_Ti21']
    x2 = data[year].loc[0,'RHi_Ti21']
    HREL = np.append(x1, x2) / 100.0
    PMSL = data[year].loc[:,'Pe'] / 100.0    
    
    if not os.path.exists('./output/WUFI/indoor'):
        os.makedirs('./output/WUFI/indoor')
    
    fname = './output/WUFI/indoor/' + year + '_Ti21.wac'
    
    with open(fname, mode='w', encoding='ANSI') as f:
        if 'jok' in year:
            f.writelines(WUFI_wac_headers_indoor_jok[0] + '\n')
            f.writelines(WUFI_wac_headers_indoor_jok[1] + '\n')
            f.writelines(WUFI_wac_headers_indoor_jok[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,len(WUFI_wac_headers_indoor_jok)-1):
                f.writelines(WUFI_wac_headers_indoor_jok[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_indoor_jok[-1].split(' ')) + '\n')
            
        elif 'van' in year:
            f.writelines(WUFI_wac_headers_indoor_van[0] + '\n')
            f.writelines(WUFI_wac_headers_indoor_van[1] + '\n')
            f.writelines(WUFI_wac_headers_indoor_van[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,len(WUFI_wac_headers_indoor_van)-1):
                f.writelines(WUFI_wac_headers_indoor_van[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_indoor_van[-1].split(' ')) + '\n')

        for t in range(8760):
            txt = '{:<.2f}\t{:<.2f}\t{:<.2f}'
            vals = [TA[t], HREL[t], PMSL[t]]
            linetowrite = txt.format(*vals)
            f.write(linetowrite + '\n')
            
    # Export indoor data to WUFI files, Ti ~ S2
    x1 = data[year].loc[1:,'Ti_S2']
    x2 = data[year].loc[0,'Ti_S2']
    TA = np.append(x1, x2)
    x1 = data[year].loc[1:,'RHi_TiS2']
    x2 = data[year].loc[0,'RHi_TiS2']
    HREL = np.append(x1, x2) / 100.0
    PMSL = data[year].loc[:,'Pe'] / 100.0    
    
    if not os.path.exists('./output/WUFI/indoor'):
        os.makedirs('./output/WUFI/indoor')
    
    fname = './output/WUFI/indoor/' + year + '_TiS2.wac'
    
    with open(fname, mode='w', encoding='ANSI') as f:
        if 'jok' in year:
            f.writelines(WUFI_wac_headers_indoor_jok[0] + '\n')
            f.writelines(WUFI_wac_headers_indoor_jok[1] + '\n')
            f.writelines(WUFI_wac_headers_indoor_jok[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,len(WUFI_wac_headers_indoor_jok)-1):
                f.writelines(WUFI_wac_headers_indoor_jok[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_indoor_jok[-1].split(' ')) + '\n')
            
        elif 'van' in year:
            f.writelines(WUFI_wac_headers_indoor_van[0] + '\n')
            f.writelines(WUFI_wac_headers_indoor_van[1] + '\n')
            f.writelines(WUFI_wac_headers_indoor_van[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,len(WUFI_wac_headers_indoor_van)-1):
                f.writelines(WUFI_wac_headers_indoor_van[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_indoor_van[-1].split(' ')) + '\n')

        for t in range(8760):
            txt = '{:<.2f}\t{:<.2f}\t{:<.2f}'
            vals = [TA[t], HREL[t], PMSL[t]]
            linetowrite = txt.format(*vals)
            f.write(linetowrite + '\n')