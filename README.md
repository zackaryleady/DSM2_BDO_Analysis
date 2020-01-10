# DSM2_BDO_Analysis
A workflow for developing, analyzing, and visualizing the DSM2 runs used for developing OMR Scenarios for the WIIN Act. DSM2 is a 1D-hydrodynamic model of the Sacramento-San Joaquin Delta developed by the California Department of Water Resources that is capable of simulating 1D flow, velocity, eletrical conductivity, and particle tracking. This analysis only uses the DSM2 hydro module which is used for flow/velocity simulations given a set of input boundary conditions. No data is provided with this code, but rather it serves a version control and a portal for providing access for how the analysis is conducted. The MIT license only applies to the code provided here and not to any of the embedded auxillary code or DSM2 itself. All standard disclaimer things apply. If you have serious questions feel free to make an issue, pull request, or email zackaryleady@gmail.com or zleady@usbr.gov.  

The following are the directions for how to run the tools provided that you have a functioning Anaconda Python environment setup and this repository.  

1.) Download this repository using git or "download zip" file option  
2.) Unzip if needed  
3.) Open your Anaconda 3 Prompt and activate the required virtual environment  
4.) You should already have an Excel file with a forecast scenario   
5.) You should already have a baseline DSM2 run  
6.) Execute the TomToDSM2_pyhecdss.py tool located under the pre-processor folder:  
```
>python C:\location\to\TomToDSM2_pyhecdss.py -c C:\location\to\Excel.xlsx -f C:\location\to\forecast.dss -d C:\location\to\dicu.dss -fs 2019-02-05 -fe 2019-02-25 -sd B
```
7.) After execution of the TomToDSM2_pyhecdss.py tool you should open the forecast.dss and finish duplicating the records that only have an A record so that all records have an A record and a B record.  
8.) Copy/paste the 4 .dss files into the Data Folder in the Near-Term study and execute the two DSM2 runs (Baseline & Scenario), while modifying the config_forecast.inp file from RUN ID A to RUN ID B in between running the Baseline and the Scenario.  
9.) Copy/paste the 2 .h5 files and the CVP_BDO_WIIN.dss file into your folder  
10.) Execute the dsm2bdoomr_post_pyhecdss.py tool located in the post-processing folder:  
```
>python C:\location\to\dsm2bdoomr_post_pyhecdss.py --dirdss C:\location\to\dss_folder --dirh5 C:\location\to\h5_folder -r test_zack_20190205_20190225 -nd {'A':'Baseline','B':'OMR-7000'} -fs 2019-02-05 -fe 2019-02-25
```
11.) Once finished you should have the .csv table files necessary to read into the database for the visualization tool  
12.) Execute the dsm2bdoomr_genfigreport.py tool located in the post-processing folder:  
```
>python C:\location\to\dsm2bdoomr_genfigreport.py --dirData C:\location\to\csv_folder --run_id test_zack_20190205_20190225 -fs 2019-02-05 -fe 2019-02-25 -w C:\location\to\folder\to\write\results
```
At this point you should have all the csv tables needed to update the visualization tool's database and have the figures needed for reporting, automatically generated. Do not proceed if you do not have these results.  

To run the **visualization tool** you will use a local host environment using Python's Django library. Make sure your environment has Django.  
1.) Before running the visualization tool, the database needs to be created/updated with the new data.  
2.) If this is the first time using this repo then there is no database (i.e. no db.sqlite3 file in the same folder as the manage.py file), to create the database for the first time you need to run the following commands after you change your working directory to where the manage.py file is located:  
```
>cd C:\location\to\web_local_clean_application\bdo_dsm2_app_Github
```
```
>python manage.py makemigrations
```
```
>python manage.py migrate
```
3.) Now you should have a db.sqlite3 file in your C:\location\to\web_local_clean_application\bdo_dsm2_app_Github directory. But it doesn't actually have any data in it.  
4.) To add your new data to a new or existing database simply execute the following command from the C:\location\to\web_local_clean_application\bdo_dsm2_app_Github working directory:  
```
>python manage.py populate_db --tables_folder C:\location\to\output\csv_folder
```
This should take approximately 25 minutes to complete (Zack is working on a faster read-in)  
5.) Now your visualization tool should be ready and you can start a local host version to open in your browser by executing the following command:  
```
>python manage.py runserver
```
And then go to the address it responds with usually 127.0.0.1:8000.  

You should now have a fully function web visualization on your computer (it will not be deployed to the actual web so your friend can't see it on their computer without having their own version).  
