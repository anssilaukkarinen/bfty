# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 20:47:01 2019
Author: Anssi Laukkarinen, anssi.laukkarinen@tuni.fi

If you find any errors, please send email to the address above.

For the current status of code and license information, see:
https://github.com/anssilaukkarinen/bfty

"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def main(data_all, year_names, year_name_titles):
    
    d = {}
    
    for year_name in year_names:
        
        if 'jok' in year_name:
            latitude = 60.81
            longitude = 23.50
        elif 'van' in year_name:
            latitude = 60.33
            longitude = 24.96
        else:
            print('Error in location!')
            
        year_name_title = year_name_titles[year_name]
        
        obj = LWrad(data_all[year_name], latitude, longitude, \
                    year_name, year_name_title)
        d[year_name] = obj
        
    return(d)
    
    
    



class LWrad():
    """
    Run calculations and export results for one year
    The longwave radiation is calculated for 
    """
    
    
    def __init__(self, data, latitude, longitude, year_name, year_name_title):
        """
        "data" is a pandas dataframe of one building physical test year
        """
        
        # Imports and preparations
        self.data = data
        self.latitude_rad = latitude * (np.pi/180)
        self.longitude_deg = longitude
        self.year_name = year_name
        self.year_name_title = year_name_title
        self.sigma_SB = 5.67e-8
        
        # T and RH in the input data are instantaneous values, but the 
        # radiation values are average values for the preceding hour.
        # The radiation values are kept intact, but the T and RH are 
        # interpolated so that there is a better match of the timestamps.
        Te_on_hour = data.loc[:,'Te'].values
        Te_half_hour = np.zeros(len(Te_on_hour))
        Te_half_hour[0:-1] = Te_on_hour[0:-1] + 0.5*(Te_on_hour[1:] - Te_on_hour[0:-1])
        Te_half_hour[-1] = Te_on_hour[-1]
        
        RHe_on_hour = data.loc[:,'RHe_water'].values
        ve_on_hour = self.calc_v(Te_on_hour, RHe_on_hour)
        ve_half_hour = np.zeros(len(ve_on_hour))
        ve_half_hour[0:-1] = ve_on_hour[0:-1] + 0.5*(ve_on_hour[1:]-ve_on_hour[0:-1])
        ve_half_hour[-1] = ve_on_hour[-1]
        
        vesat_half_hour = self.calc_v(Te_half_hour, 100.0)
        RHe_half_hour = 100.0 * (ve_half_hour/vesat_half_hour)
        
        
        self.T_dew = self.calc_T_dew(Te_half_hour, RHe_half_hour)
        self.T_air = Te_half_hour + 273.15
        self.I_glob = data.loc[:,'Rglob'].values
        
        
        
        # Calculations
        self.calc_K_t()
        
        self.epsilon_sky = 1.5357 \
                    + 0.5981*(self.T_dew/100) \
                    - 0.5687*(self.T_air/273.15) \
                    - 0.2799*self.K_t
        
        self.LWdn = self.epsilon_sky * self.sigma_SB * self.T_air**4
        
        self.T_sky = (self.LWdn/self.sigma_SB)**0.25
        
        self.dT_sky = self.T_sky - self.T_air
        
        
        # Export results
        if not os.path.exists('LWrad'):
            os.makedirs('LWrad')
        
        self.make_plots()
        
        self.export_intermediate_results_to_csv()
        self.export_final_results_to_csv()
    
    
    @staticmethod
    def calc_v(T, RH):
        """
        Calculate the water vapour concentration from T and RH, kg/m3
        RH is given with respect to liquid water
        CIMO guide measurement of humidity
        """
        
        psat = 611.2 * np.exp((17.62*T) / (243.12+T))
        v = (RH/100.0) * psat / (461.5*(273.15+T))
        return(v)
    
    
    def calc_T_dew(self, T, RH):
        """
        Calculates the dew point temperature from air temperature
        and relative humidity
        """
        psat = (RH/100.0) * 611.2 * np.exp((17.62*T)/(234.12+T))
        
        theta_dew = np.log(psat/611.2)*234.12 / (17.62 - np.log(psat/611.2))
        
        return(theta_dew)
        
    
    def calc_K_t(self):
        """
        Calculates the clearness index
        
        It is assumed that the data starts from Jan 1st 00:00
        and lasts for 8760 hours
        
        The measured solar radiation is the mean flux from the previous hour,
        so dt = 0.5 hours has been added to time stamps to align the 
        longwave radiation calculation with the average time of the solar
        radiation measurement. The first value in the Rglob column corresponds 
        to 00:30, so the adding dt gives: 
        idx = 0 -> 00:30, idx = 1 -> 01:30, etc
        """
        
        t = np.arange(8760) + 0.5
        
        # Declination angle
        self.declination_rad = 23.45 * (np.pi/180) * np.sin(2*np.pi * (t-1944)/8760)
        
        # Time of day
        self.CL = np.tile(np.arange(24)+0.5, 365)
        
        # Equation of time
        self.Gamma = 2*np.pi * (t/8760.0)
        dummy1 = 0.0075 \
                + 0.1868*np.cos(self.Gamma) \
                - 3.2077*np.sin(self.Gamma) \
                - 1.4615*np.cos(2*self.Gamma) \
                -4.089*np.sin(2*self.Gamma)
        self.ET = 2.2918*dummy1
        
        # Apparent solar time
        self.AST = self.CL + self.ET/60.0 + (self.longitude_deg-30)/15.0
        
        # Hour angle
        self.omega_rad = (np.pi/180) * 15 * (self.AST - 12.0)
        
        # Solar constant
        self.I_sc = 1367.0
        
        # Eccentricity factor
        self.r = 1 + 0.033 * np.cos(2*np.pi*(t-3*24)/8760)
        
        # Solar radiation to horizontal surface without atmosphere
        dummy2 = np.cos(self.latitude_rad) * np.cos(self.declination_rad) * np.cos(self.omega_rad) \
                + np.sin(self.latitude_rad) * np.sin(self.declination_rad)
        self.I_0 = self.r * self.I_sc * dummy2
        
        # Clearness index
        self.K_t_days = np.zeros((365*2,2))
        t_half_morning = 9
        t_half_evening = 3
        
        for day in range(365):
            # Loop through all the days
            
            # Morning
            I_0_morning = self.I_0[(day*24):(day*24+13)]
            I_glob_morning = self.I_glob[(day*24):(day*24+13)]
            
            I_0_morning_sum = np.sum(I_0_morning[I_0_morning > 0])
            I_glob_morning_sum = np.sum(I_glob_morning[I_0_morning > 0])
            
            if I_0_morning_sum > 0.0:
                t_half_morning = 13 - np.sum(I_0_morning > 0)/2
                self.K_t_days[day*2, 1] = I_glob_morning_sum/I_0_morning_sum
            else:
                self.K_t_days[day*2, 1] = 0.5
            
            self.K_t_days[day*2, 0] = day*24 + t_half_morning
        
            
            # Evening
            I_0_evening = self.I_0[(day*24+13):((day+1)*24)]
            I_glob_evening = self.I_glob[(day*24+13):((day+1)*24)]
            
            I_0_evening_sum = np.sum(I_0_evening[I_0_evening > 0])
            I_glob_evening_sum = np.sum(I_glob_evening[I_0_evening > 0])
            
            if I_0_evening_sum > 0.0:
                t_half_evening = np.sum(I_0_evening > 0)/2
                self.K_t_days[day*2+1, 1] = I_glob_evening_sum/I_0_evening_sum
            else:
                self.K_t_days[day*2+1, 1] = 0.5
                
            self.K_t_days[day*2+1, 0] = day*24 + 13 + t_half_evening
        
        
        self.K_t = np.interp(np.arange(8760), self.K_t_days[:,0], self.K_t_days[:,1])
        
    
    def make_plots(self):
        """
        This function creates plots from LWdn, emissivity_sky and dT_sky
        Temperature difference between air and sky is defined as:
        LWdn = emissivity_sky * sigma * T_air**4 = 1 * sigma * T_sky**4
        """
        
        
        plt.figure(figsize=(4,3))
        plt.plot(self.LWdn)
        plt.title(self.year_name_title)
        plt.xlabel('Time from the beginning of the year, h')
        plt.ylabel('LWdn, W/m$^2$')
        plt.axis([0, 8760, 125, 450])
        plt.grid()
        plt.savefig('./LWrad/LWdn_' + self.year_name + '.png', \
                    dpi=200, bbox_inches='tight')
        plt.close()
        
        plt.figure(figsize=(4,3))
        plt.plot(self.epsilon_sky)
        plt.title(self.year_name_title)
        plt.xlabel('Time from the beginning of the year, h')
        plt.ylabel('Effective sky emissivity, -')
        plt.axis([0, 8760, 0.60, 1.05])
        plt.grid()
        plt.savefig('./LWrad/Emissivity_' + self.year_name + '.png', \
                    dpi=200, bbox_inches='tight')
        plt.close()
        
        plt.figure(figsize=(4,3))
        plt.plot(self.T_sky)
        plt.title(self.year_name_title)
        plt.xlabel('Time from the beginning of the year, h')
        plt.ylabel('Tsky,eff, K')
        plt.axis([0, 8760, 220, 300])
        plt.grid()
        plt.savefig('./LWrad/Tskyeff_' + self.year_name + '.png', \
                    dpi=200, bbox_inches='tight')
        plt.close()
        
        plt.figure(figsize=(4,3))
        plt.plot(self.dT_sky)
        plt.title(self.year_name_title)
        plt.xlabel('Time from the beginning of the year, h')
        plt.ylabel('dT = Tsky - Tair, $\degree$C')
        plt.axis([0, 8760, -30, 5])
        plt.grid()
        plt.savefig('./LWrad/dTsky_' + self.year_name + '.png', \
                    dpi=200, bbox_inches='tight')
        plt.close()
        
        
    def export_intermediate_results_to_csv(self):
        """
        This function exports hourly values of Tair, Tdew, 
        Iglob, I0 and Kt to a csv file
        """
        
        dummy = np.array((self.T_air, self.T_dew, \
                          self.I_glob, self.I_0, self.K_t)).T
        np.savetxt('./LWrad/'+self.year_name+'_Tair_Tdew_Iglob_I0_Kt.csv', \
                   dummy, \
                   fmt='%-10.3f', \
                   header='Tair(K)   Tdew(degC) Iglob(W/m2)  I0(W/m2)   Kt(-)')
        
        
        
    def export_final_results_to_csv(self):
        """
        This function exports LWdn, emissivity_sky, T_sky 
        and dT_sky to csv files
        """
        
        dummy = np.array((self.LWdn, self.epsilon_sky, \
                          self.T_sky, self.dT_sky)).T
        np.savetxt('./LWrad/'+self.year_name + '_LWdn_emissivity_Tsky_dTsky.csv', \
                   dummy, fmt=['%10.2f', '%10.3f', '%15.2f', '%15.2f'], \
                   header='LWdn(W/m2)  emis_sky(-)     T_sky(K)       dTsky(degC)')
        

        
        
if __name__ == '__main__':
    
    year_names = ['jok2004', 'jok2030', 'jok2050', 'jok2100', \
                  'van2007', 'van2030', 'van2050', 'van2100']
    
    year_name_titles = {'jok2004':'Jokioinen 2004', \
                    'jok2030':'Jokioinen 2030', \
                    'jok2050':'Jokioinen 2050', \
                    'jok2100':'Jokioinen 2100', \
                    'van2007':'Vantaa 2007', \
                    'van2030':'Vantaa 2030', \
                    'van2050':'Vantaa 2050', \
                    'van2100':'Vantaa 2100'}
    
    
    
    ##
    
    fname = './input/bf_test_years_2020-04-20.xlsx'
    data_all = pd.read_excel(fname, sheet_name=year_names)
    
    output = main(data_all, year_names, year_name_titles)
    
