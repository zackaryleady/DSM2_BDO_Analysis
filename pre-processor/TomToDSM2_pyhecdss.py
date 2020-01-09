# Required imported python libraries
# Python default libraries, no need to install
import os
import datetime
import sys
import logging
import argparse
# This tool originally used vtools (written by Jon Shu CADWR)
# to read *.dss data, but vtools required Py2.7
# This tool now uses pyhecdss which is a tool written by Nicky Sandhu for Py3.*
# Current github repo for pyhecdss:
# https://github.com/CADWRDeltaModeling/pyhecdss
import pyhecdss
# Data manipulation libraries
import pandas as pd

# Global pyhecdss variables
pyhecdss.set_message_level(0)  # 0 is little output 10 is all output
pyhecdss.set_program_name('PYTHON')


def CreateLogger(log_file):
    """ Zack's Generic Logger function to create onscreen and file logger

    Parameters
    ----------
    log_file: string
        `log_file` is the string of the absolute file pathname for writing the
        log file too, which is a mirror of the onscreen log display.

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
    # Create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Create error file handler and set level to info
    handler = logging.FileHandler(log_file,  "w", encoding=None, delay="true")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def valid_scenario_id(c):
    """ An ArgParse Validator for Scenario ID Input by the User on CMD

    The argparse library can accept a user created validation function for
    custom data types. This function makes sure that the input is a capital
    letter. If the letter is 'A' then the function double checks with a cmd
    line prompt to double check that the user wants to over-ride the baseline.
    Typically 'A' is reserved as the baseline identifier for running DSM2
    scenarios from DWR OCO's Excel WorkSheet.

    Parameters
    ----------
    c: string
        `c` must be a capital letter formatted as a string

    Returns
    -------
    c: string
        `c` is returned unchanged if it passes the logic tests

    Raises
    ------
    AssertionError:
        `msg` is passed to argparse.ArgumentTypeError to stop the script at
        the command line input checks/parsing to immediately notify the user

    """
    try:
        assert c >= 'A'
        assert c <= 'Z'
        if c == 'A':
            ans = input("Are you sure you want to use 'A'? \n" +
                        "'A' is typically used as the baseline identifier?"
                        + "[Y/N]")
            if not ans == 'Y':
                sys.exit(0)
        return c
    except AssertionError:
        msg = "Not a valid single uppercase letter: '{}'.".format(c)
        raise argparse.ArgumentTypeError(msg)


def valid_date(s):
    """ An ArgParse Validator for Forecast Start & End Input by the User on CMD

    The argparse library can accept a user created validation function for
    custom data types. This function checks the input `s` which is a string
    date and attempts to convert it to a pandas datetime TimeStamp. If the
    datetime conversion fails, the function raises an error.

    Parameters
    ----------
    s: string (date)
        `s` is a date string input from the user for either the
        --forecast_start or --forecast_end command line input

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
        msg = "Not a valid date: '{0}' must be YYYY-MM-DD.".format(s)
        raise argparse.ArgumentTypeError(msg)


def ExtractExcelToDF(ini_dict, mapping_dict):
    """ Tom's OMR Forecast Excel WorkSheet Extractor to Pandas Dataframe

    Reads the Excel file sent by Tom for BDO DSM2 Scenario Data. The column
    names are mapped in the mapping_dict to the DSM2 part B and C in the
    forecast.dss file. The purpose of this function is to only retrieve the
    data specified by the mapping_dict keys and the datetime range determined
    by the --forecast_start and --forecast_end command line arguments provided
    by the user. These arguments are already converted as pandas datetime
    TimeStamps by the valid_date function during the parsing of the argparse
    command line args.

    Parameters
    ----------
    ini_dict: dict
        `ini_dict` is the initialization dictionary created by parsing the
        vars(args) into the ini_dict variable. The dictionary has key:value
        pairs such as 'forecast_start'='2018-09-09', etc.

    mapping_dict: dict
        `mapping_dict` is a static dictionary defined under main. It directly
        maps the names contained in Tom's Excel WorkSheet to the part B and C
        names of the forecast.dss file.

    Returns
    -------
    var_selection: pandas DataFrame
        `var_selection` is a dataframe containing only the variables defined as
        keys in the mapping dictionary and only the datetimes between the
        --forecast_start time and the --forecast_end time specified
        by the user.

    Notes
    -----
    If the variable names change in the mapping dictionary then a different
    selection will be made.

    """
    # the absolute filepathname to Tom's Excel WorkBook / WorkSheet
    excel_path = ini_dict.get("convert")
    # the forecast_start date input as --forecast_start and changed to pandas
    # datetime by the valid_date function during parsing of the cmd argparse
    # arguments
    start_date = ini_dict.get("forecast_start")
    # the forecast_end date input as --forecast_end and changed to pandas
    # datetime by the valid_date function during parsing of the cmd argparse
    # arguments
    end_date = ini_dict.get("forecast_end")
    # creates a datetime range from start to end at a daily frequency
    datetime_range = pd.date_range(start=start_date, end=end_date, freq='D')
    # reads the Excel file sent by Tom for BDO DSM2 Scenario Data
    # usecols set manually by reviewing the excel file
    # header set manually by reviewing the excel file
    # sheetname set manually by reviewing the excel file
    df_data = pd.read_excel(excel_path, sheet_name='DATA', header=2,
                            usecols=list(range(0, 25)))
    # restricts dataframe to only the index rows in the datetime_range
    time_selection = df_data.loc[(df_data['DATE'].isin(datetime_range))]
    # changes dataframe index to the DATE column
    time_selection.set_index('DATE', inplace=True)
    # restricts dataframe to only the variables in the mapping_dict keys
    var_selection = time_selection.loc[:, mapping_dict.keys()]
    for col in ['CCF', 'TPP']:
        # quick conversion
        var_selection.loc[:, col] /= 1.983
    return var_selection


def Retrieve_DICU_DssRecord(dss_file):
    """ Reads the *.dss Record from DICU.dss for the DICU BBID Constant

    Reads the B=BBID and C=DIV-FLOW record from the DICU.dss file in order to
    retrieve the DICU BBID Constant. Some logic matches the month of the
    forecast_start and forecast_end command line arguments with the *.dss
    record to obtain the BBID constant which is then subtracted from the
    clifton court forebay input data to create the banks record in the
    CreateForecastBanksDss function contained in this tool.

    Parameters
    ----------
    dss_file: string
        `dss_file` the absolute file pathname for the DICU.dss file provided
        by the "dicu" command line argument

    Returns
    -------
    temp_df: pandas DataFrame
        `temp_df` is a pandas dataframe containing a single record for the
        *.dss record containing Bpart="BBID" and Cpart="DIV-FLOW". This is
        a monthly constant value extracted from the DICU.dss file in order to
        derive the banks record

    Notes
    -----
    This function will stop the tool if more than 1 record is found in the
    DICU.dss file matching Bpart="BBID" and Cpart="DIV-FLOW". In the future,
    this should be changed to use try/except clauses.

    """
    # the selector string for the Bpart of the *.dss record pathname
    selector_B = "BBID"
    # the selector string for the Cpart of the *.dss record pathname
    selector_C = "DIV-FLOW"
    logging.info("Retrieving selector_B={}, selector_C={} from \n {}"
                 .format(selector_B, selector_C, dss_file))
    # creates an open pyhecdss *.dss file object
    # similiar to with open(file) as f: commonly used in python
    dss_file_obj = pyhecdss.DSSFile(dss_file)
    # returns a pandas dataframe with the *.dss pathnames broken-up into
    # columns from /A/B/C/D/E/F/, this is filterable by pandas column logic
    catalog_df = dss_file_obj.read_catalog()
    # selects the catalog rows that have columns B & C equal to selector B & C
    selection = catalog_df.loc[(catalog_df['B'] == selector_B) &
                               (catalog_df['C'] == selector_C)]
    # returns list of complete *.dss pathnames from a catalog pandas dataframe
    pathnames_lst = dss_file_obj.get_pathnames(selection)
    if not len(pathnames_lst) == 1:
        logging.error('More than one dss record found for {},{} \n {}'
                      .format(selector_B, selector_C, pathnames_lst))
        sys.exit(0)
    else:
        logging.info("Success: single record isolated for {},{}"
                     .format(selector_B, selector_C))
        # reads the *.dss record in a pandas dataframe
        temp_df, temp_unit, temp_type = dss_file_obj.read_rts(pathnames_lst[0])
    dss_file_obj.close()
    return temp_df


def CreateForecastBanksDss(df_excel, ini_dict, df_CHWST000, mapping_dict):
    """ Derives the Forecast Banks Record

    The forecast Banks record is created from the existing Clifton Court
    Forebay record in the df_excel DataFrame subtracting the BBID constant
    selected by month from the df_CHWST000 DataFrame which came from the
    Retrieve_DICU_DssRecord. This involves a not so great selection of the
    "correct" month by comparing the months contained in the --forecast_start
    and the --forecast_end arguments and either making sure they are equal or
    using the --forecast_end month if they are not. The month is then used
    to select the monthly BBID constant from the df_CHWST000 record. Once the
    Banks record is created in the DataFrame an entry is added for Banks in
    the mapping dictionary. Both df_excel and mapping_dict are modified
    inplace (mutated).

    Parameters
    ----------
    df_excel: pandas DataFrame
        `df_excel` the primary pandas DataFrame read from Tom's Data Excel
        Sheet. (df_excel is renamed df_banks once it contains the Banks record)

    ini_dict: dict
        `ini_dict` is the initialization dictionary created by parsing the
        vars(args) into the ini_dict variable. The dictionary has key:value
        pairs such as 'forecast_start'='2018-09-09', etc.

    df_CHWST000: pandas DataFrame
        `df_CHWST000` is the DataFrame that contains the BBID constant data
        record extracted from the DICU *.dss record in the
        Retrieve_DICU_DssRecord function. It is used to obtain the month
        selected BBID constant.

    mapping_dict: dict
        `mapping_dict` is a static dictionary defined under main. It directly
        maps the names contained in Tom's Excel WorkSheet to the part B and C
        names of the forecast.dss file.

    Returns
    -------
    df_excel: pandas DataFrame
        `df_excel` the primary pandas DataFrame to which the 'Banks' column
        or record is added too. After this function it is renamed to df_banks.

    mapping_dict: dict
        `mapping_dict` is a static dictionary defined under main. It directly
        maps the names contained in Tom's Excel WorkSheet to the part B and C
        names of the forecast.dss file. In this function it is mutated to
        include a 'Banks' record.


    Notes
    -----
    The way the 'Banks' record is created here is not recommended in the
    general case, but is rather a pseudo-shortcut in this workflow.

    """
    # the forecast_start date input as --forecast_start and changed to pandas
    # datetime by the valid_date function during parsing of the cmd argparse
    # arguments
    start_date = ini_dict.get("forecast_start")
    # the forecast_end date input as --forecast_end and changed to pandas
    # datetime by the valid_date function during parsing of the cmd argparse
    # arguments
    end_date = ini_dict.get("forecast_end")
    # creates start month variable from --forecast_start argument
    start_month = start_date.month
    # creates end month variable from --forecast_end argument
    end_month = end_date.month
    # test that start_month and end_month are equal
    # if they are not equal obtain the DICU BBID constant from end_month
    try:
        assert start_month == end_month
        logging.info("--forecast_start month and --forecast_end month are" +
                     "equal {} == {}".format(start_month, end_month))
    except AssertionError as e:
        logging.warning(e)
        logging.warning("Taking month from --forecast_end argument for" +
                        "retrieving the DICU BBID constant")
    logging.info("DICU BBID constant from month: {}".format(end_month))
    # extracts the bbid_constant from the df_CHWST000 DataFrame by month
    bbid_constant = (df_CHWST000.loc["{}-{}-01"
                                     .format(end_date.year, end_month),
                                     :].values)
    bbid_constant = float(bbid_constant)
    logging.info("bbid_constant = {}".format(bbid_constant))
    # creates BANKS column in df_excel dataframe
    df_excel['BANKS'] = df_excel['CCF'] - bbid_constant
    # adds new key:value pair for BANKS in mapping_dict
    mapping_dict["BANKS"] = {"B": "CHSWP003", "C": "FLOW-EXPORT"}
    return df_excel, mapping_dict


def WriteToForecastDss(df_banks, ini_dict, mapping_dict):
    """ Writes the Forecast (Scenario Data) to the forecast.dss file

    Main operation function of generating the forecast Scenario data
    and writing it to the forcast.dss file. This function splices the scenario
    data from df_banks (formerly df_excel) into the *.dss records within the
    forecast.dss file and writes them out as the scenario data (usually B
    instead of A). A special clause also derives the yolo scenario data by
    combining sacweir and freweir data. This function does not duplicate all
    the necessary records but only modifies the records that require data
    splicing within the --forecast_start and --forecast_end. The direct
    duplicate records should be done manually after this tool.

    Parameters
    ----------
    df_banks: pandas DataFrame
        `df_banks` formerly df_excel is the primary pandas DataFrame read
        from Tom's Data Excel Sheet. df_banks also contains the derived Banks
        data from CreateForecastBanksDss

    ini_dict: dict
        `ini_dict` is the initialization dictionary created by parsing the
        vars(args) into the ini_dict variable. The dictionary has key:value
        pairs such as 'forecast_start'='2018-09-09', etc.

    mapping_dict: dict
        `mapping_dict` is a static dictionary defined under main. It directly
        maps the names contained in Tom's Excel WorkSheet to the part B and C
        names of the forecast.dss file. At this point mapping_dict has a key
        for Banks.

    Notes
    -----
    This function does not duplicate all the *.dss records needed for running
    the scenario DSM2 run. Certain *.dss records that just require duplication,
    but not data splicing must be done manually in the forecast.dss file after
    this tool is finished running. This is done on purpose to force the modeler
    to check there work as a QAQC point.

    """
    # series of onscreen print checks
    logging.info('Current ini_dict is:')
    logging.info(ini_dict)
    logging.info('Current mapping_dict is:')
    logging.info(mapping_dict)
    # creates a datatime range from --forecast_start to --forecast_end
    dt = pd.date_range(ini_dict.get("forecast_start"),
                       ini_dict.get("forecast_end"), freq='1D', normalize=True)
    # loops through all the columns in the primary dataframe df_banks
    for bcol in df_banks.columns.tolist():
        logging.info('Working on: {}'.format(bcol))
        # gets the value list from the mapping_dict which is Bpart/Cpart
        searcher = mapping_dict.get(bcol)
        logging.info('Found {} as {} in mapping_dict'.format(bcol, searcher))
        # creates a selector search variable for Bpart/Cpart for pyhecdss
        selector_B = searcher.get("B")
        selector_C = searcher.get("C")
        # creates a file object from the forecast.dss file
        dss_file_obj = pyhecdss.DSSFile(ini_dict.get("forecast"))
        # returns a pandas dataframe with the *.dss pathnames broken-up
        # into columns from /A/B/C/D/E/F/, this is filter-able by pandas
        # column logic
        catalog_df = dss_file_obj.read_catalog()
        # if claused used to skip over Yolo variable which is handled later
        if not selector_B == 'BYOLO040':
            # selects a *.dss record based on the Bpar/Cpart with Fpart
            # containing A as A is a reserved letter for the Baseline
            selection = catalog_df.loc[(catalog_df['B'] == selector_B) &
                                       (catalog_df['C'] == selector_C) &
                                       (catalog_df['F'].str.contains("A"))]
            # returns list of complete *.dss pathnames from a catalog
            # pandas dataframe
            pathnames_lst = dss_file_obj.get_pathnames(selection)
            assert len(pathnames_lst) == 1
            temp_df, temp_unit, temp_type = (dss_file_obj
                                             .read_rts(pathnames_lst[0]))
            # loop that replaces old dss record values with new scenario value
            for indx in dt:
                temp_df.loc[indx, pathnames_lst[0]] = df_banks.loc[indx, bcol]
            # splits up old pathname for creating the new scenario pathname
            new_pathname_split = pathnames_lst[0].split("/")
            new_pathname_letter = (new_pathname_split[6]
                                   .replace("A", ini_dict.get("scenario_id")))
            new_pathname_split[6] = new_pathname_letter
            # rejoins new pathname with Fpart containing scenario_id letter
            new_pathname = '/'.join(new_pathname_split)
            temp_df = temp_df.shift(1, freq='D')
            # writes new data to the new pathname inside the forecast.dss file
            dss_file_obj.write_rts(new_pathname, temp_df, temp_unit, temp_type)
            logging.info('Wrote dss record to forecast.dss: \n {}'
                         .format(new_pathname))
        # Code to handle creating and updating the BYOLO040 variable for YOLO
        elif selector_B == 'BYOLO040':
            # YOLO is SACWEIR + FREWEIR
            df_banks['YOLO'] = df_banks['SACWEIR'] + df_banks['FREWEIR']
            # makes sure that SACWEIR and FREWEIR are mapped to same
            # dss record finder
            assert mapping_dict.get("SACWEIR") == mapping_dict.get("FREWEIR")
            yolo_B = mapping_dict.get("SACWEIR").get("B")
            yolo_C = mapping_dict.get("SACWEIR").get("C")
            # selects a *.dss record based on the Bpar/Cpart with Fpart
            # containing A as A is a reserved letter for the Baseline
            selection = catalog_df.loc[(catalog_df['B'] == yolo_B) &
                                       (catalog_df['C'] == yolo_C) &
                                       (catalog_df['F'].str.contains("A"))]
            pathnames_lst = dss_file_obj.get_pathnames(selection)
            assert len(pathnames_lst) == 1
            yolo_df, yolo_unit, yolo_type = (dss_file_obj
                                             .read_rts(pathnames_lst[0]))
            # loop that replaces old dss record values with new scenario value
            for indx in dt:
                yolo_df.loc[indx, pathnames_lst[0]] = (df_banks.loc[indx,
                                                                    'YOLO'])
            # splits up old pathname for creating the new scenario pathname
            new_pathname_split = pathnames_lst[0].split("/")
            new_pathname_letter = (new_pathname_split[6]
                                   .replace("A", ini_dict.get("scenario_id")))
            new_pathname_split[6] = new_pathname_letter
            # rejoins new pathname with Fpart containing scenario_id letter
            new_pathname = '/'.join(new_pathname_split)
            yolo_df = yolo_df.shift(1, freq='D')
            # writes new data to the new pathname inside the forecast.dss file
            dss_file_obj.write_rts(new_pathname, yolo_df, yolo_unit, yolo_type)
            logging.info('Wrote yolo record to forecast.dss: \n {}'
                         .format(new_pathname))
    dss_file_obj.close()
    return 0


if __name__ == "__main__":
    # begins global runtime clock
    start = datetime.datetime.now()
    # creates a parser object from argparse library for cmd line args
    parser = argparse.ArgumentParser()
    parser.add_argument("--convert", "-c", type=str,
                        help="Provide the absolute file pathname to the \
                        Input Data Excel file from Tom for BDO DSM2 \
                        simulation")
    parser.add_argument("--forecast", "-f", type=str,
                        help="Provide the absolute file pathname to the \
                        forecast input *.dss file that Ian provided")
    parser.add_argument("--dicu", "-d", type=str,
                        help="Provide the absolute filepath name to the \
                        dicu input *.dss file that Ian provided")
    parser.add_argument("--forecast_start", "-fs", type=valid_date,
                        help="Provide a valid forecast start date \
                        e.g. 2018-08-23")
    parser.add_argument("--forecast_end", "-fe", type=valid_date,
                        help="Provide a valid forecast end date \
                        e.g. 2018-08-24")
    parser.add_argument("--scenario_id", "-sd", type=valid_scenario_id,
                        help="Provide a single capital letter as the scenario \
                        id to be used in the *.dss file as an unique \
                        identifier. The baseline scenario is usually 'A'. So \
                        the scenario id is usually 'B'")
    # creates an args object from the parsed user input
    args = parser.parse_args()
    # assigns args object into a pythong dictionary
    ini_dict = vars(args)
    # creates global logger object for logging
    abspath = os.path.abspath(__file__)
    pydir_name = os.path.dirname(abspath)
    log_file = os.path.join(pydir_name, "log_TomToDSM2_{}.log"
                            .format(datetime.datetime.date(start)))
    CreateLogger(log_file)
    # records the initialize command line arguments provided by the user
    for k in ini_dict.keys():
        logging.info("user key input: {} \n set to: {}".format(k, ini_dict.
                                                               get(k)))
    # User notes:
    # if key == 'YOLO' then SACWEIR + FREWEIR = Yolo Bypass == BYOLO040
    # Banks (CHSWP003) = (CHWST000 (CCF From Tom's Excel Sheet) -
    # 'BBID/DIV-FLOW')
    # BBID/DIV-FLOW from DICU.dss file
    # Banks must be put in with forecast.dss file and the other nodes in the
    # mapping dictionary including CCF
    # mappings dictionary key(Tom): [Bpart,Cpart]
    mapping_dict = {"CCF": {"B": "CHWST000", "C": "FLOW-ALLOTMENT"},
                    "TPP": {"B": "CHDMC004", "C": "FLOW-EXPORT"},
                    "VNS": {"B": "RSAN112", "C": "FLOW"},
                    "FPT": {"B": "RSAC155", "C": "FLOW"},
                    "CAL": {"B": "RCAL009", "C": "FLOW"},
                    "MOKE": {"B": "RMKL070", "C": "FLOW"},
                    "COS": {"B": "RCSM075", "C": "FLOW"},
                    "SACWEIR": {"B": "BYOLO040", "C": "FLOW"},
                    "FREWEIR": {"B": "BYOLO040", "C": "FLOW"}}
    # records the initial mapping_dictionary keys and values
    for k in mapping_dict.keys():
        logging.info("mapping dictionary key: {} \n set to: {}".format(k,
                     mapping_dict.get(k)))
    # Tom's OMR Excel Sheet to pandas DataFrame
    df_excel = ExtractExcelToDF(ini_dict, mapping_dict)
    logging.info(df_excel)
    # Banks intermediate derivation from dicu.dss file
    df_CHWST000 = Retrieve_DICU_DssRecord(ini_dict.get("dicu"))
    logging.info(df_CHWST000)
    # Creates Bank record for writing to forecast.dss file
    df_banks, mapping_dict = CreateForecastBanksDss(df_excel, ini_dict,
                                                    df_CHWST000, mapping_dict)
    logging.info(df_banks)
    # Writes all new data to forecast.dss including Banks and Yolo
    WriteToForecastDss(df_banks, ini_dict, mapping_dict)
    # stop global runtime clock
    elapsed_time = datetime.datetime.now() - start
    # displays runtime
    logging.info("Runtime: {} seconds".format(elapsed_time))
