# bfty (Building Physical Test Years)

### How to use
The code was written with Python 3. You can use git clone to create a working copy of the repository, but if you don't have git installed, you can also download the repository as a zip-file, extract it and run the py-files that way. Run first `LWrad.py` and secondly `climate_files.py`.

The Delphin 6 outdoor climatic files need to be first converted to a c6b file using the CCMEditor, available at: https://www.bauklimatik-dresden.de/downloads.php

### Background and description of the files
This repository contains data and code for creating input files for building physical simulation programs. The building physics research group at Tampere University of Technology (currently Tampere University) coordinated the FRAME-project during 2009-2012, in which two moisture test years were selected for current climate (1980-2009), 2050-climate (2035-2064) and 2100-climate (2085-2114), summing up to six years in total. These years were Jokioinen 2004, 2050 and 2100 for structures that are mainly influenced by outdoor air humidity and Vantaa 2007, 2050 and 2100 for structures where the main moisture source is driving rain. The 30-year climatic data for the current and future climates was provided by the Finnish Meteorological Institute, which had parallel projects called REFI-A for building energy consumption and indoor air conditions test years and REFI-B for building physical test years. The folder `input` contains hourly data on the Finnish building physical test years for current and future climate.

The original test year data did not include atmospheric downward longwave radiation, which can however affect the hygrothermal behaviour of building envelope structures. To improve on this matter, different semi-empirical models presented in literature were tested and eventually one of them was chosen to calculate the atmospheric downward longwave radiation for the building physical test years. The `LWrad.py` file uses the selected model and the data from the building physical test years to calculate hourly longwave radiation values that can be used as part of the test years. The longwave radiation data is written to the folder `LWrad`.

In addition to the longwave radiation data, the file `climate_files.py` includes code that reads in the original test year and longwave radiation data and outputs new data files that can be used as an input for building physical simulation programs. The output files are currently csv files for general purpose use; ccd files for Delphin 5 and Delphin 6; and wac files WUFI Pro and WUFI 2D. The files are written to the folder `output`.

The purpose of this GitHub repository is to teach myself on how to use GitHub and to be an easy-access-no-guarantee distribution channel for the appended climate files. Hopefully the material will find use!

### References (mostly in Finnish)

1. J. Vinha, A. Laukkarinen, M. Mäkitalo, S. Nurmi, P. Huttunen, T. Pakkanen, P. Kero, E. Manelius, J. Lahdensivu, A. Köliö, K. Lähdesmäki, J. Piironen, V. Kuhno, M. Pirinen, A. Aaltonen ja J. Suonketo, Ilmastonmuutoksen ja lämmöneristyksen lisäyksen vaikutukset vaipparakenteiden kosteusteknisessä toiminnassa ja rakennusten energiankulutuksessa, Tampereen teknillinen yliopisto. Rakennustekniikan laitos: 2013, http://urn.fi/URN:ISBN:978-952-15-2949-8.
2. K. Jylhä, T. Kalamees, H. Tietäväinen, K. Ruosteenoja, J. Jokisalo, R. Hyvönen, S. Ilomets, S. Saku ja A. Hutila, Rakennusten energialaskennan testivuosi 2012 ja arviot ilmastonmuutoksen vaikutuksista, Ilmatieteen laitos. Raportteja - Rapporter - Reports 2011:6, http://hdl.handle.net/10138/33069.
3. K. Ruosteenoja, K. Jylhä, H. Mäkelä, R. Hyvönen, P. Pirinen ja I. Lehtonen, Rakennusfysiikan testivuosien sääaineistot havaitussa ja arvioidussa ilmastossa : REFI-B -hankkeen tuloksia, Ilmatieteen laitos. Raportteja - rapporter - Reports 2013 :1, http://hdl.handle.net/10138/38648.
4. Mundt Petersen, S & Wallentén, P 2014, Methods for compensate lack of climate boundary data. in M Quattrone & J Vanderley (eds), Proceedings XIII DBMC - XIII International Conference on Durability of Building Materials and Components. pp. 632-639, XIII International Conference on Durability of Building Materials and Components, 2014, São Paulo, Brazil, 2014/09/02.
5. T. Jokela, Kipsilevytuulensuojallisten puurunkoisten ulkoseinien rakennusfysikaalinen toiminta, Tampereen yliopisto, rakennustekniikka 2018, http://urn.fi/URN:NBN:fi:tty-201811262762.
6. T. Jokela, A. Laukkarinen ja J. Vinha, Ilmakehän pitkäaaltoinen säteily rakennusfysikaalisissa laskentatarkasteluissa, Rakennusfysiikka 2019. Uusimmat tutkimustulokset ja hyvät käytännön ratkaisut. 2019, http://urn.fi/URN:NBN:fi:tuni-202002202255 
7. A. Laukkarinen, P. Kero ja J. Vinha, Condensation at the exterior surface of windows, Journal of Building Engineering, vol 19, pp. 592-601. 2018, https://doi.org/10.1016/j.jobe.2018.06.014.
8. Ilmatieteen laitos, ”Rakennusfysiikan ilmastolliset testivuodet,” [Online]. Available: https://www.ilmatieteenlaitos.fi/rakennusfysiikan-ilmastolliset-testivuodet. 
9. Tampereen yliopisto, rakennusfysiikan tutkimusryhmä, ”Rakennusfysikaaliset testivuodet,” [Online]. Available: https://research.tuni.fi/rakennusfysiikka/kosteusanalysointimenetelma/rakennusfysikaaliset-testivuodet/.
