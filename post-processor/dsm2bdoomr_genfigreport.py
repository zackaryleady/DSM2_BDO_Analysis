# Required imported python libraries
# Python default libraries, no need to install
import os
import sys
import datetime
import logging
import argparse
# Data manipulation libraries
import numpy as np
import pandas as pd
# Graphing libraries
import plotly.graph_objs as go
import plotly.io as pio
# Statistical analysis libraries
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp


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


def Get_CSV_Data(csv_table_name, data_dir):
    """ Helper Function for Reading *.csv Tables into Pandas DataFrames

    Parameters
    ----------
    csv_table_name: string
        `csv_table_name` is the straight table name outputted by the
        dsm2bdoomr_post_pyhecdss tool, e.g. HydroTable.csv.

    data_dir: string
        `data_dir` is the directory containing the *.csv files provided by
        the user via --dirData input argument from the command line.

    Returns
    -------
    csv_table_df: pandas DataFrame
        `csv_table_df` the read-in pandas DataFrame of the *.csv table.

    """
    # creates the absolute file pathname for the *.csv table
    csv_table_path = os.path.join(data_dir, csv_table_name)
    # reads the *.csv table into a pandas DataFrame
    csv_table_df = pd.read_csv(csv_table_path, sep=",", header=0,
                               parse_dates=True, infer_datetime_format=True)
    return csv_table_df


def MakeSummaryTable(hydrotable_df, ini_dict, summary_range='full'):
    """ Creates a Summary Data Table

    This function creates an exact replica of any 1 of the 3 summary tables
    contained in the visualization using the HydroTable. The summary_range
    argument has 3 options of 'full', 'five', and 'fourteen'; which become
    the number of days that the summary contains for the means.

    Parameters
    ----------
    hydrotable_df: pandas DataFrame
        `hydrotable_df` is the DataFrame containing the HydroTable.csv data

    ini_dict: dict
        `ini_dict`is the initialization dictionary from the cmd arguments
        provided by the user.

    summary_range: string
        `summary_range` is specified as 'full', 'five', or 'fourteen' in order
        to determine the Timedelta for creating the datetime_range to select
        for calculating the summary mean. e.g. 'five' means that the summary
        mean will only include the first five days from the forecast start,
        whereas 'full' is the entire forecast period.

    Returns
    -------
    fig: Plotly figure object
        `fig` is the python representation of the Plotly figure to be written
        out to a *.png. Plotly is able to represent basic data-tables as a
        special Plotly trace named go.Table().

    Notes
    -----
    Currently the datetimes and timedeltas from the summary range argument are
    determined from the runid; however, it might be better for them to come
    from the arguments of --forecast_start and --forecast_end.

    """
    # obtain the runid for date parsing from the initialization dictionary
    runid = ini_dict.get("run_id")
    # runid is formatted with the last two _ components being the dates
    # the start_date is the second from the end so -2 is used to index
    runid_start_date = pd.to_datetime(runid.split("_")[-2],
                                      yearfirst=True, format='%Y%m%d')
    # checks that the --forecast_start arg and the runid start are equal
    forecast_start = ini_dict.get("forecast_start")
    assert runid_start_date == forecast_start
    start_date = runid_start_date
    if summary_range == 'full':
        # if the entire forecast period is used then parse the forecast end
        runid_end_date = pd.to_datetime(runid.split("_")[-1],
                                        yearfirst=True, format='%Y%m%d')
        forecast_end = ini_dict.get("forecast_end")
        assert runid_end_date == forecast_end
        end_date = runid_end_date
    elif summary_range == 'five':
        # if only 5 days then use pandas Timedelta to create the end date
        end_date = start_date + pd.Timedelta('5 days')
    elif summary_range == 'fourteen':
        # if only 14 days then use pandas Timedelta to create the end date
        end_date = start_date + pd.Timedelta('14 days')
    logging.info("Summary Table type: {} starts: {} ends: {}"
                 .format(summary_range, start_date, end_date))
    # creates the datetime_range for selection from the HydroTable DataFrame
    datetime_range = pd.date_range(start=start_date, end=end_date,
                                   freq='15T')
    # select date range from HydroTable DataFrame
    selection = hydrotable_df.loc[(hydrotable_df['datetime']
                                   .isin(datetime_range))]
    # sub-select only certain columns
    selection = selection[['variable', 'scenario', 'channel', 'datetime',
                           'value']]
    # groupby and then aggregate the value column as a mean
    summary = selection.groupby(['variable', 'scenario', 'channel']).agg(
                                {'value': 'mean'})
    # table configuration
    summary = summary.unstack(['variable', 'scenario'])
    summary.columns = summary.columns.droplevel()
    scenario_name_lst = (summary.columns.unique(level='scenario').values
                         .tolist())
    omr_name_lst = [x for x in scenario_name_lst if 'OMR' in x]
    assert len(omr_name_lst) == 1
    omr_name = omr_name_lst[0]
    # creates the 'Difference' column seen in the summary tables
    add_diff = summary.loc[:, pd.IndexSlice[:, omr_name]].sub(
                           summary.loc[:, pd.IndexSlice[:, 'Baseline']].values,
                           1).rename(columns={omr_name: 'Difference'})
    summary = summary.join(add_diff).sort_index(axis=1, level='variable',
                                                sort_remaining=False)
    # rename columns from variable names to human readable
    summary = summary.rename(columns={'FLOW': 'Average Daily Flow (cfs)',
                                      'VEL': 'Average Daily Velocity (ft/s)'})
    summary = summary.round(2)
    # create Table object from Plotly
    header_vals = [('Type', 'Scenario', 'Channel')]
    cell_vals = [summary.index.values.tolist()]
    for col_val in list(summary.columns):
        new_col = col_val + ("",)
        header_vals.append(new_col)
        cell_vals.append(summary[col_val].values.tolist())
    trace = go.Table(
            header=dict(values=header_vals,
                        fill=dict(color='#C2D4FF')),
            cells=dict(values=cell_vals, fill=dict(color='#F5F8FF'))
            )
    data = [trace]
    layout = go.Layout(autosize=False, width=1500, height=1000)
    fig = go.Figure(data=data, layout=layout)
    return fig


def MakeChannelNodeTable(runid, hydrotable_df):
    """ Creates the Channel Node Tables (Mean Flow or Mean Velocity)

    This function creates an exact replica of the 2 summary tables for either
    Mean Flow or Mean Velocity. The function does not have a trigger for either
    Mean Flow or Mean Velocity internally as the hydrotable_df that is provided
    as an input already has been selected for either Flow or Velocity, while
    the normal hydrotable_df has both.

    Parameters
    ----------
    runid: string
        `runid` is just the --run_id user input from the cmd and stored in the
        ini_dict object. It should be formatted as:
        4letters_4letters_ForecastStart_ForecastEnd

    hydrotable_df: pandas DataFrame
        `hydrotable_df` is the DataFrame containing the HydroTable.csv data

    Returns
    -------
    fig1: Plotly figure object
        `fig1` is the python representation of the Plotly figure to be written
        out to a *.png. Plotly is able to represent basic data-tables as a
        special Plotly trace named go.Table().

    fig2: Plotly figure object
        `fig2` is the python representation of the Plotly figure to be written
        out to a *.png. Plotly is able to represent basic data-tables as a
        special Plotly trace named go.Table().

    Notes
    -----
    The use of fig1 and fig2 is just to match the visualization which uses
    two table figures for the Mean Flow and Mean Velocity summary node tables
    because using all 8 nodes in one table makes the table text small in order
    to prevent text overlapping. That is to say this is a visual convience
    decision.

    """
    # lists of the node numbers
    eight_nodes = ['CHAN012', 'CHAN049', 'CHAN050', 'CHAN094', 'CHAN124',
                   'CHAN148', 'CHAN422', 'CHAN423']
    first_nodes = ['CHAN012', 'CHAN049', 'CHAN050', 'CHAN094']
    second_nodes = ['CHAN124', 'CHAN148', 'CHAN422', 'CHAN423']
    # dates determined from runid splitting not
    # --forecast_start or --forecast_end arguments
    start_date = pd.to_datetime(runid.split("_")[-2], yearfirst=True,
                                format='%Y%m%d')
    end_date = pd.to_datetime(runid.split("_")[-1], yearfirst=True,
                              format='%Y%m%d')
    # create datetime_range from start and end date parsing
    datetime_range = pd.date_range(start=start_date, end=end_date,
                                   freq='15T')
    # selection made on hydrotable_df
    selection = (hydrotable_df.loc[(hydrotable_df['channel']
                 .isin(eight_nodes)) &
                 (hydrotable_df['datetime'].isin(datetime_range))])
    # selection of dataframe columns on selection variable
    selection = selection[['channel', 'scenario', 'datetime', 'value']]
    grouper = selection.groupby(['channel', 'scenario',
                                 pd.Grouper(key='datetime', freq='D')])
    result = grouper['value'].mean()
    daily = result.unstack(['channel', 'scenario'])
    scenario_name_lst = daily.columns.unique(level='scenario').values.tolist()
    omr_name_lst = [x for x in scenario_name_lst if 'OMR' in x]
    assert len(omr_name_lst) == 1
    omr_name = omr_name_lst[0]
    # make new baseline minus omr column
    add_diff = daily.loc[:, pd.IndexSlice[:, omr_name]].sub(
                         daily.loc[:, pd.IndexSlice[:, 'Baseline']].values,
                         1).rename(columns={omr_name: 'Difference'})
    daily = daily.join(add_diff).sort_index(axis=1, level='channel',
                                            sort_remaining=False)
    # break down dataframe into first and second node dataframe for two tables
    first_df = daily.loc[:, daily.columns.get_level_values('channel').isin(
                         first_nodes)]
    second_df = daily.loc[:, daily.columns.get_level_values('channel').isin(
                          second_nodes)]
    first_df = first_df.round(2)
    second_df = second_df.round(2)
    first_df.index = pd.to_datetime(first_df.index)
    first_df.index = first_df.index.date
    second_df.index = pd.to_datetime(second_df.index)
    second_df.index = second_df.index.date
    # embedded helper function for trace making (undocumented)

    def make_trace(df):
        header_vals = [('Channel', 'Scenario')]
        cell_vals = [df.index.values.tolist()]
        for col_val in list(df.columns):
            header_vals.append(col_val)
            cell_vals.append(df[col_val].values.tolist())
        trace = go.Table(
                    header=dict(values=header_vals,
                                fill=dict(color='#C2D4FF')),
                    cells=dict(values=cell_vals, fill=dict(color='#F5F8FF'))
                    )
        return trace
    # creates Plotly table objects
    trace1 = make_trace(first_df)
    trace2 = make_trace(second_df)
    layout = dict(autosize=False, width=1500, height=900)
    fig1 = go.Figure(data=[trace1], layout=layout)
    fig2 = go.Figure(data=[trace2], layout=layout)
    return fig1, fig2


def Make_ECDF_Graphs(df, ini_dict, output_graphs):
    """ Generates the Full ECDF Graphs and KS Statistic for Reporting

    This function creates the ECDF graphs as exact replicas of the ECDF graphs
    shown on the visualization home page. They are designed for comparing the
    ECDFs of the baseline/scenario against each other for flow or velocity.
    The generic goal here is to show either a significant different or not in
    the flow and velocity fields between the two scenarios. The KS-statistic
    is used as a metric to quantify the difference between the two ECDFs with
    a single number. ECDF graphs are only created for the channels in the
    embedded channel_lst object. These are hard-coded for report generation
    purposes.

    Parameters
    ----------
    df: pandas DataFrame
        `df` is the DataFrame created from reading in the VarTotal.csv file.

    ini_dict: dict
        `ini_dict` is the initialization dictionary from the cmd user inputs
        read in by the argparse library. Format: {"run_id":"test"}

    output_graphs: string
        `output_graphs` is the absolute folder pathname created from the
        combining of the --write argument and 'graphs' to output the generated
        ECDF graphs from this function.

    """
    # determined variables to create graphs for
    variable_lst = ['FLOW', 'VEL']
    # determined channels to create graphs for
    channel_lst = [6, 9, 12, 21, 49, 50, 54, 81, 94, 107, 124, 148, 160, 173,
                   310, 434]
    # loops through each variable and channel combo to create an ECDF graph
    for variable in variable_lst:
        for channel in channel_lst:
            # selects data for isolating the value column
            select_baseline_data = df.loc[(df['variable'] == variable) &
                                          (df['scenario'] == 'Baseline') &
                                          (df['channel'] == channel)]
            select_scenario_data = df.loc[(df['variable'] == variable) &
                                          (df['scenario'].str
                                           .contains('OMR')) &
                                          (df['channel'] == channel)]
            # turns the value column into a numpy array
            baseline_data_arr = (select_baseline_data.value
                                 .to_numpy(dtype=np.float32))
            scenario_data_arr = (select_scenario_data.value
                                 .to_numpy(dtype=np.float32))
            logging.info("Baseline ECDF shape: {}"
                         .format(baseline_data_arr.shape))
            logging.info("Scenario ECDF shape: {}"
                         .format(scenario_data_arr.shape))
            # creates the ECDF from the numpy array (statsmodels)
            baseline_ecdf_obj = ECDF(baseline_data_arr)
            scenario_ecdf_obj = ECDF(scenario_data_arr)
            # creates the KS-statistic from the numpy array (scipy)
            KS_obj = ks_2samp(baseline_data_arr, scenario_data_arr)
            KS_stat = round(KS_obj.statistic, 4)
            # creates Plotly graph
            baseline_trace = go.Scatter(x=baseline_ecdf_obj.x,
                                        y=baseline_ecdf_obj.y,
                                        mode='lines', name='Baseline')
            scenario_trace = go.Scatter(x=scenario_ecdf_obj.x,
                                        y=scenario_ecdf_obj.y,
                                        mode='lines', name='OMR Scenario')
            KS_annotation = [go.layout.Annotation(x=0, y=1.10,
                                                  xref='paper',
                                                  yref='paper',
                                                  showarrow=False,
                                                  text='Kolmogorov-Smirnov ' +
                                                  'Distance: {}'
                                                  .format(KS_stat))]
            if variable == 'FLOW':
                var_name = 'Flow'
                unit_name = 'CFS'
            elif variable == 'VEL':
                var_name = 'Velocity'
                unit_name = 'FT/S'
            xt = "{} in {}".format(var_name, unit_name)
            yt = "Fraction of Data"
            layout = go.Layout(autosize=False, width=1500, height=900,
                               annotations=KS_annotation,
                               legend_orientation="v",
                               xaxis=dict(title=dict(text=xt)),
                               yaxis=dict(title=dict(text=yt)))
            ecdf_fig = go.Figure(data=[baseline_trace, scenario_trace],
                                 layout=layout)
            output_ecdf = os.path.join(output_graphs,
                                       "ecdf_{}_{}.png"
                                       .format(variable, channel))
            # writes Plotly graph as a *.png image
            pio.write_image(ecdf_fig, output_ecdf)
            logging.info('Wrote ECDF Graph for {} {}: \n {}'
                         .format(variable, channel, output_ecdf))
    return 0


def TableMain(ini_dict):
    """Executes the primary logic for creating Plotly Table Figures

    Main logic for generating summary tables or mean flow / mean velocity
    tables for reporting, which are replicas of those contained under
    the Data Tables tab in the visualization tool. This utilizes the
    post-processed *.csv outputs not the SQL database.

    Parameters
    ----------
    ini_dict: dict
        `ini_dict` is the initialization dictionary from the cmd user inputs
        read in by the argparse library. Format: {"run_id":"test"}

    """
    output_tables = os.path.join(ini_dict.get("write"), 'tables')
    if not os.path.exists(output_tables):
        os.mkdir(output_tables)
    hydro_csv_df = Get_CSV_Data('HydroTable.csv', ini_dict.get("dirData"))
    hydro_csv_df['datetime'] = hydro_csv_df['datetime'].apply(pd.to_datetime)
    hydro_fig = MakeSummaryTable(hydro_csv_df, ini_dict,
                                 summary_range='full')
    output_hydro = os.path.join(output_tables, 'FullSummaryT1.png')
    pio.write_image(hydro_fig, output_hydro)
    logging.info('Wrote Hydro Table: \n {}'.format(output_hydro))
    variable_dict = {'FLOW': {1: 'MeanFlowT2-1', 2: 'MeanFlowT2-2'},
                     'VEL': {1: 'MeanVelT3-1', 2: 'MeanVelT3-2'}}
    for variable in list(variable_dict.keys()):
        hydro_variable_df = hydro_csv_df.loc[(hydro_csv_df['variable']
                                              == variable)].copy()
        var_fig1, var_fig2 = MakeChannelNodeTable(ini_dict.get("run_id"),
                                                  hydro_variable_df)
        logging.info("Table variable: {}, first name: {}, second name: {}"
                     .format(variable, variable_dict.get(variable).get(1),
                             variable_dict.get(variable).get(2)))
        output_table1 = os.path.join(output_tables,
                                     '{}.png'.format(variable_dict
                                                     .get(variable).get(1)))
        output_table2 = os.path.join(output_tables,
                                     '{}.png'.format(variable_dict
                                                     .get(variable).get(2)))
        pio.write_image(var_fig1, output_table1)
        pio.write_image(var_fig2, output_table2)
        logging.info('Wrote {}: \n {}'
                     .format(variable_dict.get(variable).get(1),
                             output_table1))
        logging.info('Wrote {}: \n {}'
                     .format(variable_dict.get(variable).get(2),
                             output_table2))
    return 0


def GraphMain(ini_dict):
    """Executes the primary logic for creating Plotly Graph Figures

    Main logic for generating the ECDF graphs and KS statistic for reporting,
    which are replicas of those contained on the home page of the visualization
    tool. This utilizes the post-processed *.csv outputs not the SQL database.

    Parameters
    ----------
    ini_dict: dict
        `ini_dict` is the initialization dictionary from the cmd user inputs
        read in by the argparse library. Format: {"run_id":"test"}

    """
    channel_lst = [6, 9, 12, 21, 49, 50, 54, 81, 94, 107, 124, 148, 160, 173,
                   310, 434]
    total_csv_df = Get_CSV_Data('VarTotal.csv', ini_dict.get("dirData"))
    total_csv_df = total_csv_df.loc[(total_csv_df['channel']
                                     .isin(channel_lst))].copy()
    total_csv_df['datetime'] = total_csv_df['datetime'].apply(pd.to_datetime)
    output_graphs = os.path.join(ini_dict.get("write"), 'graphs')
    if not os.path.exists(output_graphs):
        os.mkdir(output_graphs)
    Make_ECDF_Graphs(total_csv_df, ini_dict, output_graphs)
    return 0


if __name__ == "__main__":
    # begin the code's start clock
    start = datetime.datetime.now()
    # create the command line parser object from argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dirData", type=str,
                        help="Provide full folder pathname for the \
                        Data directory.")
    parser.add_argument("--run_id", type=str,
                        help="Provide the run_id.")
    parser.add_argument("--forecast_start", "-fs", type=valid_date,
                        help="Provide the forecast start date in the \
                        YYYY-MM-DD format")
    parser.add_argument("--forecast_end", "-fe", type=valid_date,
                        help="Provide the forecast end date in the \
                        YYYY-MM-DD format")
    parser.add_argument("--write", "-w", type=str,
                        help="Provide full folder pathname for the \
                        output directory")
    args = parser.parse_args()
    ini_dict = vars(args)
    # determine the absolute file pathname of this *.py file
    abspath = os.path.abspath(__file__)
    # from the absolute file pathname determined above,
    # extract the directory path
    dir_name = os.path.dirname(abspath)
    # creates the log file pathname which is an input to CreateLogger
    log_name = os.path.join(dir_name, "log_report_{}.log".format(start.date()))
    # generic CreateLogger function which creates two loggers
    # one for the logfile write out and one for the on-screen stream write out
    logger = CreateLogger(log_name)
    for k in ini_dict.keys():
        logging.info("user key input: {} \n set to: {}".format(k, ini_dict.
                                                               get(k)))
    # Execute Main Operational Code
    TableMain(ini_dict)
    GraphMain(ini_dict)
    # Write out runtime
    elapsed_time = datetime.datetime.now() - start
    logging.info('Runtime: {} seconds'.format(elapsed_time))
