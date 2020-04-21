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


col_names = ['Te', 'RHe_water', 'RHe_ice', \
             'Ti_21', 'RHi_Ti21', \
             'Ti_S2', 'RHi_TiS2', \
             'ws', 'wd', 'precip', \
             'Rdif', 'Rdir', 'Rbeam', \
             'LWdn', \
             'Pair']

D5_keywords = ['TEMPER C', 'RELHUM %', 'RELHUM %', \
               'TEMPER C', 'RELHUM %', \
               'TEMPER C', 'RELHUM %', \
               'WINDVEL m/s', 'WINDDIR Deg', 'HORRAIN l/m2h', \
               'DIFRAD W/m2', 'DIRRAD W/m2', \
               'SKYEMISS W/m2', \
               'GASPRESS Pa']

D6_names = ['Temperature C', 'RelativeHumidity %', 'RelativeHumidity %', \
            'Temperature C', 'RelativeHumidity %', \
            'Temperature C', 'RelativeHumidity %', \
            'WindVelocity m/s', 'WindDirection Deg', 'RainFluxHorizontal l/m2h', \
            'SWRadiationDiffuse W/m2', 'SWRadiationDirect W/m2', 'DirectRadiationNormal W/m2', \
            'LWRadiationSkyEmission W/m2', \
            'AirPressure Pa']

test_year_names = ['Jokioinen 2004', 'Jokioinen 2030', \
                   'Jokioinen 2050', 'Jokioinen 2100', \
                   'Vantaa 2007', 'Vantaa 2030', \
                   'Vantaa 2050', 'Vantaa 2100']


WUFI_wac_headers_jok = ['WUFI®_WAC_02', \
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

WUFI_wac_headers_van = ['WUFI®_WAC_02', \
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


window_width = 24



# Read
data = pd.read_excel('./input/bf_test_years_2020-04-20.xlsx', \
                     sheet_name=None)


# Calculate and write files

for idx_year, year in enumerate(data.keys()):
    
    # LWdn
    fname = './LWrad/'+year + '_LWdn_emissivity_Tsky_dTsky.csv'
    data[year]['LWdn'] = pd.read_csv(fname, sep='\s+', \
                                   usecols=[0], skiprows=0)
    
    # Pair
    data[year]['Pair'] = 101325.0 * np.ones(8760)
    
    # Rdir
    data[year]['Rdir'] = data[year]['Rglob'].values - data[year]['Rdif'].values
    
    # Indoor air, Ti = constant 21 degC, hourly
    Te = data[year].loc[:,'Te']
    RHe_water = data[year].loc[:,'RHe_water']
    ve = (RHe_water/100.0)*pvsat_water(Te) / (Rw*(273.15+Te))
    
    Ti_21 = 21.0 * np.ones(8760)
    Te_rolling_mean = Te.rolling(window_width, min_periods = 1, center=True).mean()
    ve_rolling_mean = ve.rolling(window_width, min_periods = 1, center=True).mean()
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
    fname = './output/figures/' + year + '/' + key + '.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight')
    plt.close()
    
    
    
    ## Export to csv files
    if not os.path.exists('./output/csv/'+year):
        os.makedirs('./output/csv/'+year)
    
    for idx, col_name in enumerate(col_names):
        
        fname = './output/csv/'+year+'/'+col_name+'.csv'
        
        if col_name in ['precip', 'Rdif', 'Rdir', 'Rbeam', 'LWdn']:
            # Move one hour earlier
            x1 = data[year].loc[1:,col_name].values
            x2 = data[year].loc[0,col_name]
            x = np.append(x1,x2)
        else:
            x = data[year].loc[:,col_name].values
        
        X = np.column_stack((np.arange(len(x)), x))
        
        np.savetxt(fname, X, fmt=('%-5d', '%.2f'), \
                   header='t    '+D6_names[idx], \
                   comments='')
        


    ## Export to Delphin 5 files
    if not os.path.exists('./output/Delphin5/'+year):
        os.makedirs('./output/Delphin5/'+year)
    
    dummy = [x for x in col_names if x not in ['Rbeam']]
    
    for idx, col_name in enumerate(dummy):
        
        fname = './output/Delphin5/'+year+'/'+col_name+'.ccd'
        with open(fname, 'w') as f:
            
            # Header
            linetowrite = D5_keywords[idx]
            f.write(linetowrite + '\n')
            
            # Data rows            
            if col_name in ['precip', 'Rdif', 'Rdir', 'Rbeam', 'LWdn']:
                x1 = data[year].loc[1:,col_name]
                x2 = data[year].loc[0,col_name]
                x = np.append(x1,x2)
            else:
                x = data[year].loc[:,col_name]
            
            for t in range(8760):
                hour = t % 24
                day = int((t-hour)/24)
                val = x[t]
                
                linetowrite = '{:<4d} {:02d}:00:00 {:.2f}'.format(day, hour, val)
                f.writelines(linetowrite + '\n')
    
    
    
    ## Export to Delphin 6 files
    if not os.path.exists('./output/Delphin6/'+year):
        os.makedirs('./output/Delphin6/'+year)
    
    for idx, col_name in enumerate(col_names):
        
        fname = './output/Delphin6/'+year+'/'+col_names[idx]+'.ccd'
        with open(fname, 'w') as f:
            
            # Header
            linetowrite = D6_names[idx]
            f.write(linetowrite + '\n')
            
            # Data rows
            if col_name in ['precip', 'Rdif', 'Rdir', 'Rbeam', 'LWdn']:
                x1 = data[year].loc[1:,col_name]
                x2 = data[year].loc[0,col_name]
                x = np.append(x1,x2)
            else:
                x = data[year].loc[:,col_name]
                        
            for t in range(8760):
                hour = t % 24
                day = int((t-hour)/24)
                val = data[year].loc[t,col_name]
                
                linetowrite = '{:<4d} {:02d}:00:00 {:.2f}'.format(day, hour, val)
                f.write(linetowrite + '\n')
                
                
    ## Export to WUFI files, RHe over water
    
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
    PMSL = data[year].loc[:,'Pair'] / 100.0    
    
    
    if not os.path.exists('./output/WUFI_over_water'):
        os.makedirs('./output/WUFI_over_water')
    
    fname = './output/WUFI_over_water/'+year+'.wac'
    
    with open(fname, mode='w', encoding='ANSI') as f:
        if 'jok' in year:
            f.writelines(WUFI_wac_headers_jok[0] + '\n')
            f.writelines(WUFI_wac_headers_jok[1] + '\n')
            f.writelines(WUFI_wac_headers_jok[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,11):
                f.writelines(WUFI_wac_headers_jok[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_jok[-1].split(' ')) + '\n')
            
        elif 'van' in year:
            f.writelines(WUFI_wac_headers_van[0] + '\n')
            f.writelines(WUFI_wac_headers_van[1] + '\n')
            f.writelines(WUFI_wac_headers_van[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,11):
                f.writelines(WUFI_wac_headers_van[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_van[-1].split(' ')) + '\n')

        for t in range(8760):
            txt = '{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}'
            vals = [TA[t], HREL[t], ISDH[t], ISD[t], ILAH[t], RN[t], WD[t], WS[t], PMSL[t]]
            linetowrite = txt.format(*vals)
            f.write(linetowrite + '\n')
            
            

    ## Export to WUFI files, RHe over ice
    
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
    PMSL = data[year].loc[:,'Pair'] / 100.0    
    
    
    if not os.path.exists('./output/WUFI_over_ice'):
        os.makedirs('./output/WUFI_over_ice')
    
    fname = './output/WUFI_over_ice/'+year+'.wac'
    
    with open(fname, mode='w', encoding='ANSI') as f:
        if 'jok' in year:
            f.writelines(WUFI_wac_headers_jok[0] + '\n')
            f.writelines(WUFI_wac_headers_jok[1] + '\n')
            f.writelines(WUFI_wac_headers_jok[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,11):
                f.writelines(WUFI_wac_headers_jok[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_jok[-1].split(' ')) + '\n')
            
        elif 'van' in year:
            f.writelines(WUFI_wac_headers_van[0] + '\n')
            f.writelines(WUFI_wac_headers_van[1] + '\n')
            f.writelines(WUFI_wac_headers_van[2] + test_year_names[idx_year] + '\n')
            for idx_line in range(3,11):
                f.writelines(WUFI_wac_headers_van[idx_line] + '\n')
            f.writelines('\t'.join(WUFI_wac_headers_van[-1].split(' ')) + '\n')

        for t in range(8760):
            txt = '{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}\t{:<.2f}'
            vals = [TA[t], HREL[t], ISDH[t], ISD[t], ILAH[t], RN[t], WD[t], WS[t], PMSL[t]]
            linetowrite = txt.format(*vals)
            f.write(linetowrite + '\n')