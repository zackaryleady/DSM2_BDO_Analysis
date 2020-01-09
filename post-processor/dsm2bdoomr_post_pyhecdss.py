# Required imported python libraries
# Python default libraries, no need to install
import os
import sys
import datetime
import logging
import argparse
import ast
import re
# This tool originally used vtools (written by Jon Shu CADWR)
# to read *.dss data, but vtools required Py2.7
# This tool now uses pyhecdss which is a tool written by Nicky Sandhu for Py3.*
# Current github repo for pyhecdss:
# https://github.com/CADWRDeltaModeling/pyhecdss
import pyhecdss
# Other data I/O libraries
import h5py
# Data manipulation libraries
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

# Global pyhecdss variables
pyhecdss.set_message_level(0)
pyhecdss.set_program_name('PYTHON')


def CreateLogger(log_file):
    """ Zack's Generic Logger function to create onscreen and file logger

    Parameters
    ----------
    log_file: string
        `log_file` is the string of the absolute filepathname for writing the
        log file too which is a mirror of the onscreen display.

    Returns
    -------
    logger: logging object

    Notes
    -----
    This function is completely generic and can be used in any python code.
    The handler.setLevel can be adjusted from logging.INFO to any of the other
    options such as DEBUG, ERROR, WARNING in order to restrict what is logged.

    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # create error file handler and set level to info
    handler = logging.FileHandler(log_file,  "w", encoding=None, delay="true")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def valid_date(s):
    """ An ArgParse Validator for Start & End Input by the User on CMD

    The argparse library can accept a user created validation function for
    custom data types. This function checks the input `s` which is a string
    date and attempts to convert it to a pandas datetime TimeStamp. If the
    conversion values, the function raises an error.

    Parameters
    ----------
    s: string (date)
        `s` is a date string input from the user for either the --start or
        --end command line input

    Returns
    -------
    anonymous: pandas datetime Timestamp

    Raises
    ------
    ValueError:
        `msg` is passed to argparse.ArgumentTypeError to stop the script at
        the command line input checks/parsing to immediately notify the user
        if the input date string cannot be converted

    """
    try:
        return pd.to_datetime(s, format="%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'. Must be YYYY-MM-DD.".format(s)
        logging.error(msg)
        raise argparse.ArgumentTypeError(msg)


def ConvertToRow(run_id, df):
    """ Translates the DataFrame to a row format for use in a SQL database

    The DataFrame is in a column-based format where each *.dss record is in its
    own column with a datetime index. The DataFrame is then translated to a row
    based format with roughly columns (run_id, path, unit, datetime, value).

    Parameters
    ----------
    run_id: string
        `run_id` is the unique BDO DSM2 OMR Scenario identifer that the user
        provides as an input from the command line argument --run_id.

    df: pandas DataFrame
        `df` is a column-based pandas DataFrame in the context of this tool.

    Returns
    -------
    df: pandas DataFrame object
        `df` is a row-based pandas DataFrame in the context of this tool

    """
    logging.info('Shape of dataframe before conversion in ConvertToRow {}'
                 .format(df.shape))
    df = pd.DataFrame(df.unstack())
    df.reset_index(inplace=True)
    df.columns = ['PATH', 'DATETIME', 'VALUE']
    df['PATH'], df['UNIT'] = df['PATH'].str.split(';', 1).str
    df = df[['PATH', 'UNIT', 'DATETIME', 'VALUE']]
    id_lst = [run_id]*len(df)
    df.insert(loc=0, column='RUN_ID', value=id_lst)
    logging.info('Shape of dataframe after conversion in ConvertToRow {}'
                 .format(df.shape))
    return df


def HydroScenario(df, ini_dict):
    """ Translates a row based DataFrame to a HydroTable database DataFrame

    The input DataFrame is a row-based DataFrame that is then translated to be
    an exact mirror of the HydroTable database Table in the sqlite database
    used by the web visualization/site for the BDO DSM2 OMR Scenarios.

    Parameters
    ----------
    df: pandas DataFrame
        `df` is a row based DataFrame to be converted into a HydroTable
        database DataFrame. It is likely this was created from ConvertToRow().

    ini_dict: dict
        `ini_dict` is the initialization dictionary from the cmd arguments
        provided by the user.

    Returns
    -------
    df: pandas DataFrame
        `df` is a formatted pandas DataFrame that directly mirrors the
        HydroTable in the BDO DSM2 OMR Scenario database for the website.

    """
    logging.info('Shape of dataframe before conversion in HydroScenario {}'
                 .format(df.shape))
    scenario_lst = []
    channel_lst = []
    var_lst = []
    for x in df['PATH'].tolist():
        x_split = x.split("/")
        assert len(x_split) == 8
        x_fpart = x_split[6]
        x_bpart = x_split[2]
        x_cpart = x_split[3]
        try:
            scenario_letter = re.findall('([A-Z]$)', x_fpart)
            assert len(scenario_letter) == 1
            assert scenario_letter[0].isupper()
        except AssertionError:
            try:
                scenario_letter = re.findall('([A-Z])', x_fpart)
                assert len(scenario_letter) == 1
                assert scenario_letter[0].isupper()
            except AssertionError:
                msg = ('Cannot find a capitol letter A-Z in the fpart name: {}\
                for detecting a scenario letter to create scenario name. \
                Check --name_dict argument or *.dss record {}'
                       .format(x_fpart, x))
                logging.error(msg)
                raise Exception(msg)
        try:
            scenario_name = ini_dict.get("name_dict").get(scenario_letter[0])
        except KeyError:
            msg = ('Cannot find scenario_letter: {} as dictionary key in \
                   name_dict'.format(scenario_letter))
            logging.error(msg)
            raise Exception(msg)
        scenario_lst.append(scenario_name)
        channel_lst.append(x_bpart)
        var_lst.append(x_cpart)
    df.insert(loc=2, column='VARIABLE', value=var_lst)
    df.insert(loc=3, column='CHANNEL', value=channel_lst)
    df.insert(loc=4, column='SCENARIO', value=scenario_lst)
    df.columns = [x.lower() for x in df.columns]
    logging.info('Shape of dataframe after conversion in HydroScenario {}'
                 .format(df.shape))
    return df


def H5AddVelocity(h5_dir):
    """ Calculates and Writes the Velocity dataset into each *.h5 file

    This function accepts a directory folder containing any number of output
    DSM2 *.h5 files as setup for BDO DSM2 OMR Scenario analysis for the WIIN
    Act. It then extracts the channel flow and channel area datasets from each
    *.h5 file and calculates a channel_velocity dataset from flow/area for each
    set of entries. The channel_velocity dataset is then written directly back
    into the existing *.h5 file. The function checks if the velocity dataset
    exists before performing the reads/calculations.
    This is not a generic function, and should not be used in other tools.
    WARNING: This function directly modifies the *.h5 file inplace. Make sure
    you have a backup copy before executing.

    Parameters
    ----------
    h5_dir: string
        `h5_dir` is the absolute folder pathname to the directory that contains
        the raw *.h5 files from a BDO DSM2 OMR Scenario run or set of runs.

    Notes
    -----
    This function is a replacement for Travis's (Cramer Fish Sciences)
    1.AddVelocity R Script which was modified to zack_V3 R script and then
    translated into this Python function.

    """
    logging.info('Finding *.h5 files in raw_h5 directory for Adding Velocity')
    h5_dir_lst = [f for f in os.listdir(h5_dir) if f.endswith('.h5')]
    assert len(h5_dir_lst) == 2
    for hfile in h5_dir_lst:
        logging.info('Found h5 filename: {}'.format(hfile))
        abs_hfile = os.path.join(h5_dir, hfile)
        logging.info('Reconstructed absolute file pathname as \n {}'
                     .format(abs_hfile))
        f = h5py.File(abs_hfile, 'r+')
        if '/hydro/data/channel_velocity' not in f:
            logging.info('No channel velocity dataset found, creating one' +
                         'from flow/area')
            # reads the channel flow *.h5 dataset into a numpy array
            flow = f['/hydro/data/channel flow'][()]
            # reads the channel area *.h5 dataset into a numpy array
            area = f['/hydro/data/channel area'][()]
            assert len(flow) == len(area)
            assert type(flow) == type(area)
            # calculates the velocity array
            velocity = flow/area
            assert flow[0][0][0]/area[0][0][0] == velocity[0][0][0]
            logging.info('Assert tests pasts flow: ' +
                         '{} area: {} velocity: {}'
                         .format(flow[0][0], area[0][0], velocity[0][0]))
            # writes velocity array into *.h5 channel_velocity dataset
            f.create_dataset('/hydro/data/channel_velocity', data=velocity)
            f.close()
            logging.info('Wrote velocity array to: {}'.format(hfile))
        else:
            logging.info('Channel velocity dataset detected, not rewriting')
    return 0


def H5PrepareAndExtractData(h5_dir, dir_name, name_dict):
    """ Primary Extraction Function for Writing H5 data to DataFrames

    Extracts the flow and velocity datasets from each *.h5 file in the
    h5_dir. The velocity dataset was generated by H5AddVelocity function
    contained within this tool and called before this function. The extracted
    flow and velocity datasets for each scenario/baseline is then written into
    and output_dict mapped to the scenario/baseline name from the name_dict.
    The DataFrames written to the output_dict are also ordered from the *.h5
    file based on the channel to index mapping contained in this function.

    Parameters
    ----------
    h5_dir: string
        `h5_dir` is the absolute folder pathname that contains the 2 *.h5 files
        from the output of the DSM2 runs for a BDO WIIN Act analysis.

    dir_name: string
        `dir_name` is just the absolute folder pathname for the directory that
        this tool resides in. It can be used to make new directories or
        reconstructing absolute file pathnames.

    name_dict: dict
        `name_dict` is the user inputted dictionary from the command line
        argument --name_dict that contains the key:value mapping of a
        capitol letter e.g. A that maps to the database name e.g. Baseline.

    Returns
    -------
    output_dict: dict
        `output_dict` contains the flow and velocity extracted DataFrames for
        each scenario and baseline. It is formatted as:
        output_dict = {'A': {'flow_upstream': flow_df, 'vel_upstream': vel_df}}

    """
    logging.info('Finding *.h5 files in raw_h5 directory')
    h5_dir_lst = [f for f in os.listdir(h5_dir) if f.endswith('.h5')]
    assert len(h5_dir_lst) == 2
    # placeholder dictionary
    output_dict = {}
    # loops through each *.h5 detected in the h5_dir
    for hfile in h5_dir_lst:
        logging.info('Found h5 filename: {}'.format(hfile))
        scenario_letter = re.findall('([A-Z]$)', hfile.split('.')[0])
        assert len(scenario_letter) == 1
        logging.info('Found scenario letter: {}'.format(scenario_letter))
        assert scenario_letter[0] in list(name_dict.keys())
        scenario_letter = scenario_letter[0]
        output_dict["{}".format(name_dict.get(scenario_letter))] = {}
        abs_hfile = os.path.join(h5_dir, hfile)
        logging.info('Reconstructed absolute file pathname as \n {}'
                     .format(abs_hfile))
        h5f = h5py.File(abs_hfile, 'r+')
        channel_numbers = pd.DataFrame(h5f.get('/hydro/geometry/channel_number')[:])
        # print(channel_numbers)
        # 0 is the first column of the DataFrame channel_numbers
        # This works because the column values are the channel numbers and
        # the index of the DataFrame are the index numbers
        # to_dict() makes the index the keys and the column value the values
        # for each key
        channel_index2number=channel_numbers[0].to_dict()
        channel_number2index = {value : key for key, value in channel_index2number.items()}
        # index_test = 157
        # print('This channel number for index:',index_test, ' should be 169. It is ',channel_index2number[index_test])
        # print('This channel index for channel number:', 169, ' should be ',index_test,'. It is ',channel_number2index[169])
        # for upstream / downstream determination/filtering
        channel_location = pd.DataFrame(h5f.get('/hydro/geometry/channel_location')[:], dtype=np.str)
        logging.info("Channel location: {}".format(channel_location))
        flow_data = h5f.get('/hydro/data/channel flow')
        vel_data = h5f.get('/hydro/data/channel_velocity')
        logging.info("Flow data shape: {}".format(flow_data.shape))
        logging.info("Velocity data shape: {}".format(vel_data.shape))
        assert flow_data.shape == vel_data.shape
        flow_interval_string = flow_data.attrs['interval'][0].decode('UTF-8')
        flow_start_time = pd.to_datetime(flow_data.attrs['start_time'][0]
                                         .decode('UTF-8'))
        logging.info("Flow Start Time is: {}".format(flow_start_time))
        if flow_interval_string == '15min':
            freq_string = '15T'
            logging.info("Interval string is: " +
                         "{}, detected as: {}, and freq_string is: {}"
                         .format(flow_interval_string, '15min', freq_string))
        else:
            logging.error("Interval string is: " +
                          "{} It must be '15min for this tool."
                          .format(flow_interval_string))
            sys.exit(0)
        temp_date_range = pd.date_range(flow_start_time, freq=freq_string,
                                        periods=flow_data.shape[0])
        temp_flow_df = pd.DataFrame(index=temp_date_range)
        temp_vel_df = pd.DataFrame(index=temp_date_range)
        # hard-code channel location as UPSTREAM
        location = 'UPSTREAM'
        flow_data = flow_data[()]
        vel_data = vel_data[()]
        for c in channel_number2index.keys():
            channel_index = channel_number2index.get(c)
            location_index = int(channel_location[(channel_location[0].str.
                                                   upper() == location)].index.tolist()[0])
            temp_flow_arr = flow_data[:, channel_index, location_index]
            temp_flow_df["{}".format(c)] = temp_flow_arr.astype(np.float32)
            temp_vel_arr = vel_data[:, channel_index, location_index]
            temp_vel_df["{}".format(c)] = temp_vel_arr.astype(np.float32)
        output_dict["{}".format(name_dict.get(scenario_letter))]['flow_upstream'] = temp_flow_df
        output_dict["{}".format(name_dict.get(scenario_letter))]['vel_upstream'] = temp_vel_df
    return output_dict


def H5Summary(output_dict):
    """ Creates the VarSummary.csv

    The VarSummary.csv becomes the VarSummaryTable in the SQL database for
    the visualization tool/platform.

    Parameters
    ----------
    output_dict: dict
        `output_dict` is generated by the H5PrepareandExtractData function.
        It contains the flow and velocity extracted DataFrames for
        each scenario and baseline. It is formatted as:
        output_dict = {'A': {'flow_upstream': flow_df, 'vel_upstream': vel_df}}

    Returns
    -------
    ouput_dict: dict
        `output_dict` is mutated in place to add the summary DataFrames for
        each scenario and variable. These are later combined in the MainH5
        function to output a single VarSummary.csv

    """
    # loops through each scenario/baseline key
    for scenario_key in output_dict.keys():
        # loops through each variable key e.g. FLOW/VEL
        for variable_key in list(output_dict.get(scenario_key).keys()):
            logging.info("Creating Summary DataFrame for scenario: " +
                         "{} variable: {}".format(scenario_key, variable_key))
            temp_df = output_dict.get(scenario_key).get(variable_key)
            # .describe() is a built-in pandas function the generates most of
            # the required summary information automatically
            df_summary = temp_df.describe()
            df_summary = df_summary.transpose()
            df_summary = df_summary.reset_index()
            df_summary = df_summary.rename(columns={"index": "channel",
                                                    "min": "_min",
                                                    "25%": "quant1",
                                                    "50%": "median",
                                                    "75%": "quant3",
                                                    "max": "_max"})
            # add the partial df_summary DataFrame to the output_dict inplace
            output_dict[scenario_key]["{}_summary".format(variable_key.split("_")[0])] = df_summary
    return output_dict


def MakeVarKS(df, ini_dict):
    """ Creates the VarKS.csv

    The VarKS.csv becomes the VarKSTable in the SQL database for the
    visualization tool/platform. It is specifically need to change the DSM2
    channels color for the KS distance statistic.

    Parameters
    ----------
    df: pandas DataFrame
        `df` is essentially the df_total DataFrame used for the VarTotal.csv.
        This is used to derive a DataFrame containing the KS distance
        statistic for every scenario for every variable combination.

    ini_dict: dict
        `ini_dict` is the initialization dictionary from the cmd arguments
        provided by the user.

    Returns
    -------
    var_ks: pandas DataFrame
        `var_ks` the DataFrame to be written out for the VarKS.csv which
        replicates the VarKSTable in the SQL database.

    """
    temp_records = []
    grouped_df = df.groupby(['variable', 'channel'])
    for group_name, df_group in grouped_df:
        select_baseline_data = df_group.loc[(df_group['scenario'] == 'Baseline')]
        select_scenario_data = df_group.loc[(df_group['scenario'].str
                                             .contains('OMR'))]
        baseline_data_arr = (select_baseline_data.value
                             .to_numpy(dtype=np.float32))
        scenario_data_arr = (select_scenario_data.value
                             .to_numpy(dtype=np.float32))
        KS_obj = ks_2samp(baseline_data_arr, scenario_data_arr)
        temp_records.append({'variable': group_name[0],
                             'scenario0': 'Baseline',
                             'scenario1': '{}'.format(ini_dict
                                                      .get("name_dict")
                                                      .get("B")),
                             'channel': group_name[1],
                             'ks_stat': round(KS_obj.statistic, 4)})
        # logging.info("Group name for MakeVarKS: {} completed"
        #             .format(group_name))
    var_ks = pd.DataFrame.from_records(temp_records)
    var_ks.insert(loc=0, column='run_id',
                  value=[ini_dict.get("run_id")]*len(var_ks))
    var_ks.sort_values(by=['variable', 'channel'])
    # logging.info(var_ks)
    return var_ks


def H5CutDataToForecastTime(output_dict, forecast_start, forecast_end):
    """ Shrinks the H5 DataFrames to only the Forecast Period

    Up to this point the DataFrames for all the H5 processing are the full
    length of the simulation including the warm-up period for DSM2. This
    function reduces the output information down to just the forecast period
    as specified as the time between the forecast_start and forecast_end
    arguments/inputs.

    Parameters
    ----------
    output_dict: dict
        `output_dict` is the single input/output dictionary of all the created
        and written out dataframes for the *.h5 analysis that occurs throughout
        this tool. The dataframes are the values called by unique string keys.

    forecast_start: pandas datetime
        `forecast_start` is the datetime provided by --forecast_start cmd
        argument in the format YYYY-MM-DD

    forecast_end: pandas datetime
        `forecast_end` is the datetime provided by --forecast_end cmd
        argument in the format YYYY-MM-DD

    Returns
    -------
    output_dict: dict
    `output_dict` is mutated in place reduce the size of the DataFrames for
        each scenario and variable.

    """
    forecast_date_range = pd.date_range(start=forecast_start, end=forecast_end,
                                        freq='15T')
    for scenario_key in list(output_dict.keys()):
        for variable_key in list(output_dict.get(scenario_key).keys()):
            df = output_dict.get(scenario_key).get(variable_key)
            mod_df = df.iloc[df.index.isin(forecast_date_range)]
            logging.info("Total dataframe shape reduced from {} to {}"
                         .format(df.shape, mod_df.shape))
            output_dict[scenario_key][variable_key] = mod_df
    return output_dict


def DssCutDatatoForecastTime(hydro_dataframe, forecast_start, forecast_end):
    """ Shrinks the DSS DataFrame to only the Forecast Period

    Up to this point the DataFrames for all the DSS processing are the full
    length of the simulation including the warm-up period for DSM2. This
    function reduces the output information down to just the forecast period
    as specified as the time between the forecast_start and forecast_end
    arguments/inputs.

    Parameters
    ----------
    hydro_dataframe: pandas DataFrame
        `hydro_dataframe` is the DataFrame containing the exact formatted table
        for producing the HydroTable.csv, which is a replica of the HydroTable
        in the SQL database used in the visualization.

    forecast_start: pandas datetime
        `forecast_start` is the datetime provided by --forecast_start cmd
        argument in the format YYYY-MM-DD

    forecast_end: pandas datetime
        `forecast_end` is the datetime provided by --forecast_end cmd
        argument in the format YYYY-MM-DD

    Returns
    -------
    mod_df: pandas DataFrame
        `mod_df` just a temporary name for the HydroTable DataFrame once it
        has been reduced in size to just the forecast period.
    """
    forecast_date_range = pd.date_range(start=forecast_start, end=forecast_end,
                                        freq='15T')
    mod_df = hydro_dataframe.loc[(hydro_dataframe.datetime
                                  .isin(forecast_date_range))]
    logging.info("Hydro dataframe shape reduced from {} to {}"
                 .format(hydro_dataframe.shape, mod_df.shape))
    return mod_df


def MainDSS(ini_dict, dir_name):
    """ Executes the primary logic for DSS analysis on DSM2 DSS files

    Parameters
    ----------
    ini_dict: dict
        `ini_dict` is the initialization dictionary from the cmd user inputs
        read in by the argparse library. Format: {"run_id":"test"}

    dir_name: string
        `dir_name` is the absolute folder pathname for where this python tool
        resides.

    """
    # establish the input_data pathname as input_dir variable
    dss_dir = ini_dict.get("dirdss")
    # Find *.dss files in dss_dir
    cvp_bdo_wiin_pathname = os.path.join(dss_dir, "CVP_BDO_WIIN.dss")
    logging.info("Reading CVP_BDO_WIIN *.dss file from \n{}"
                 .format(cvp_bdo_wiin_pathname))
    # Read-in CVP_BDO_WIIN.dss, which becomes HydroTable.csv
    dss_file_obj = pyhecdss.DSSFile(cvp_bdo_wiin_pathname)
    catalog_df = dss_file_obj.read_catalog()
    pathnames_lst = dss_file_obj.get_pathnames(catalog_df)
    readin_hydro_df = pd.DataFrame()
    for n in pathnames_lst:
        try:
            temp_df, temp_unit, temp_type = dss_file_obj.read_rts(n)
            temp_df.columns = ["{};{}".format(temp_df.columns.tolist()[0],
                               temp_unit)]
            readin_hydro_df = pd.concat([readin_hydro_df, temp_df], axis=1)
        except Exception as e:
            logging.error(e)
            sys.exit(0)
    dss_file_obj.close()
    logging.info(readin_hydro_df.head())
    logging.info("Read-in hydro dataframe shape: {}"
                 .format(readin_hydro_df.shape))
    # immediately write out a *.csv file for review / record-keeping
    readin_hydro_df.to_csv(os.path.join(dss_dir, "CVP_BDO_WIIN_temp.csv"),
                           sep=",")
    logging.info("Preparing to manipulate *.dss data from *.csv into " +
                 "SQLite outputs")
    # driving functions for creating HydroTable
    row_hydro_df = ConvertToRow(ini_dict.get("run_id"), readin_hydro_df)
    write_hydro_df = HydroScenario(row_hydro_df, ini_dict)
    forecast_start = ini_dict.get("forecast_start")
    forecast_end = ini_dict.get("forecast_end")
    write_hydro_df = DssCutDatatoForecastTime(write_hydro_df,
                                              forecast_start,
                                              forecast_end)
    output_folder = os.path.join(dir_name, "{}".format(ini_dict.get("run_id")))
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    hydro_output_path = os.path.join(output_folder, 'HydroTable.csv')
    write_hydro_df.to_csv(hydro_output_path, sep=",", index=False)
    logging.info("Wrote HydroTable.csv to: \n {}".format(hydro_output_path))
    return 0


def MainH5(ini_dict, dir_name):
    """ Executes the primary logic for H5 analysis on DSM2 TideFiles

    Parameters
    ----------
    ini_dict: dict
        `ini_dict` is the initialization dictionary from the cmd user inputs
        read in by the argparse library. Format: {"run_id":"test"}

    dir_name: string
        `dir_name` is the absolute folder pathname for where this python tool
        resides.

    """
    # establish a temporary h5_dir variable
    h5_dir = ini_dict.get("dirh5")
    # establish a temporary name_dict variable
    name_dict = ini_dict.get("name_dict")
    # adds velocity to *.h5 files from flow/area, if needed
    H5AddVelocity(h5_dir)
    output_dict = H5PrepareAndExtractData(h5_dir, dir_name, name_dict)
    forecast_start = ini_dict.get("forecast_start")
    forecast_end = ini_dict.get("forecast_end")
    output_dict = H5CutDataToForecastTime(output_dict,
                                          forecast_start,
                                          forecast_end)
    output_dict = H5Summary(output_dict)

    VarSummary = pd.DataFrame(columns=['run_id', 'variable', 'scenario',
                                       'channel', 'count', 'mean', 'std',
                                       '_min', 'quant1', 'median',
                                       'quant3', '_max'])
    VarTotal = pd.DataFrame(columns=['run_id', 'variable', 'scenario',
                                     'channel', 'datetime', 'value'])

    for scenario_key in output_dict.keys():
        for variable_key in output_dict.get(scenario_key).keys():
            df = output_dict.get(scenario_key).get(variable_key)
            if 'upstream' in variable_key:
                df = df.transpose()
                df = df.stack()
                df.index.names = ['channel', 'datetime']
                df = pd.DataFrame({'value': df})
                df = df.reset_index()
                df.insert(loc=0, column='scenario',
                          value=[scenario_key]*df.shape[0])
                df.insert(loc=0, column='variable',
                          value=["{}".format(variable_key.split("_")[0].upper())]*df.shape[0])
                df.insert(loc=0, column='run_id',
                          value=[ini_dict.get("run_id")]*df.shape[0])
                VarTotal = pd.concat([VarTotal, df], axis=0)
            elif 'summary' in variable_key:
                df.insert(loc=0, column='scenario',
                          value=[scenario_key]*df.shape[0])
                df.insert(loc=0, column='variable',
                          value=["{}".format(variable_key.split("_")[0].upper())]*df.shape[0])
                df.insert(loc=0, column='run_id',
                          value=[ini_dict.get("run_id")]*df.shape[0])
                VarSummary = pd.concat([VarSummary, df], axis=0)
            else:
                logging.error("Variable Key not identified as containing" +
                              "upstream or summary ERROR")
                sys.exit(0)
    logging.info("VarTotal shape: {}".format(VarTotal.shape))
    logging.info("VarSummary shape: {}".format(VarSummary.shape))
    VarKS = MakeVarKS(VarTotal, ini_dict)
    logging.info("VarKS shape: {}".format(VarKS.shape))
    output_folder = os.path.join(dir_name, "{}".format(ini_dict.get("run_id")))
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    VarTotal.to_csv(os.path.join(output_folder, "VarTotal.csv"),
                    sep=",", index=False)
    VarSummary.to_csv(os.path.join(output_folder, "VarSummary.csv"),
                      sep=",", index=False)
    VarKS.to_csv(os.path.join(output_folder, "VarKS.csv"),
                 sep=",", index=False)
    return 0


if __name__ == "__main__":
    # begin the code's start clock
    start = datetime.datetime.now()
    # create the command line parser object from argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dirdss", type=str,
                        help="Provide full folder path for *.dss directory. \
                        Only include one baseline and one scenario within dss \
                        files")
    parser.add_argument("--dirh5", type=str,
                        help="Provide full folder path for *.h5 directory. \
                        Only include one baseline and one scenario within h5 \
                        files")
    parser.add_argument("--run_id", "-r", type=str,
                        help="Unique Model Run ID for Database")
    parser.add_argument("--name_dict", "-nd", type=str,
                        help="Provide a string in python dictionary format of\
                        the basenames of each *.h5 file with a scenario name.\
                        For example, {'A':'Baseline','B':'OMR-7000'} ")
    parser.add_argument("--forecast_start", "-fs", type=valid_date,
                        help="Provide the forecast start date in the \
                        YYYY-MM-DD format")
    parser.add_argument("--forecast_end", "-fe", type=valid_date,
                        help="Provide the forecast end date in the \
                        YYYY-MM-DD format")
    args = parser.parse_args()
    ini_dict = vars(args)
    # determine the absolute file pathname of this *.py file
    abspath = os.path.abspath(__file__)
    # from the absolute file pathname determined above,
    # extract the directory path
    dir_name = os.path.dirname(abspath)
    # creates the log file pathname which is an input to CreateLogger
    log_name = os.path.join(dir_name, "log_post_{}.log"
                            .format(datetime.datetime.date(start)))
    # generic CreateLogger function which creates two loggers
    # one for the logfile write out and one for the on-screen stream write out
    logger = CreateLogger(log_name)
    logging.info("Absolute python file location: \n {}".format(abspath))
    logging.info("Absolute dir_name location: \n {}".format(dir_name))
    ini_dict["name_dict"] = ast.literal_eval(ini_dict.get("name_dict"))
    for k in ini_dict.keys():
        logging.info("user key input: {} \n set to: {}".format(k, ini_dict.
                                                               get(k)))
    # runs the two main functions
    # DSS and H5 are separate in case future logic wants to trigger them
    # indepdently
    MainDSS(ini_dict, dir_name)
    MainH5(ini_dict, dir_name)
    # end the code's clock and reports runtime
    elapsed_time = datetime.datetime.now() - start
    logging.info("Runtime: {} seconds".format(elapsed_time))
