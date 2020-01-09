import json
import pandas as pd
import numpy as np
import plotly
import plotly.graph_objs as go
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp
from wiin.models import (HydroTable,  # VarSummaryTable,
                         VarTotalTable, RunIdTable,
                         VariableTable, ScenarioTable,
                         UnitTable, VarKSTable)


def get_mapKS(runid_jsdata, scenarioid_jsdata, variableid_jsdata,
              channelid_jsdata):
    runid_query_p = RunIdTable.objects.filter(run_id=runid_jsdata)
    variable_query_p = VariableTable.objects.filter(variable=variableid_jsdata)
    scenario_query_p = ScenarioTable.objects.all()
    print(runid_query_p, variable_query_p, scenario_query_p)
    runid_query = (RunIdTable.objects.filter(run_id=runid_jsdata)
                   .values('id')[0])
    variable_query = (VariableTable.objects.filter(variable=variableid_jsdata)
                      .values('id')[0])
    scenario_query = (ScenarioTable.objects.filter(scenario=scenarioid_jsdata,
                                                   run_id=runid_query
                                                   .get('id')).values('id')[0])
    baseline_query = (ScenarioTable.objects.filter(scenario='Baseline',
                                                   run_id=runid_query
                                                   .get('id')).values('id')[0])
    print(runid_query, variable_query, scenario_query, baseline_query)
    retrieve_ks = (VarKSTable.objects.filter(run_id=runid_query.get('id'),
                                             variable=variable_query.get('id'),
                                             scenario0=baseline_query.get('id'),
                                             scenario1=scenario_query
                                             .get('id')).values('channel',
                                                                'ks_stat'))
    out = pd.DataFrame.from_records(retrieve_ks)
    out = out.set_index('channel')
    out = out.round(4)
    out_dict = out.to_dict()
    return json.dumps(out_dict.get('ks_stat'))


def get_mapgraph(runid_jsdata, scenarioid_jsdata, variableid_jsdata,
                 channelid_jsdata):
    runid_query = (RunIdTable.objects.filter(run_id=runid_jsdata)
                   .values('id')[0])
    variable_query = (VariableTable.objects.filter(variable=variableid_jsdata)
                      .values('id')[0])
    scenario_query = (ScenarioTable.objects.filter(scenario=scenarioid_jsdata,
                                                   run_id=runid_query
                                                   .get('id')).values('id')[0])
    baseline_query = (ScenarioTable.objects.filter(scenario='Baseline',
                                                   run_id=runid_query
                                                   .get('id')).values('id')[0])
    scenario_total_query = (VarTotalTable.objects
                            .filter(run_id=runid_query.get('id'),
                                    variable=variable_query.get('id'),
                                    scenario=scenario_query.get('id'),
                                    channel=channelid_jsdata)
                            .values('datetime', 'value'))
    baseline_total_query = (VarTotalTable.objects
                            .filter(run_id=runid_query.get('id'),
                                    variable=variable_query.get('id'),
                                    scenario=baseline_query.get('id'),
                                    channel=channelid_jsdata)
                            .values('datetime', 'value'))
    df_scenario = pd.DataFrame.from_records(scenario_total_query)
    df_baseline = pd.DataFrame.from_records(baseline_total_query)
    if variableid_jsdata == 'FLOW':
        var_name = 'Flow'
        unit_name = 'CFS'
    elif variableid_jsdata == 'VEL':
        var_name = 'Velocity'
        unit_name = 'FT/S'
    baseline_data_arr = df_baseline.value.to_numpy(dtype=np.float32)
    scenario_data_arr = df_scenario.value.to_numpy(dtype=np.float32)
    baseline_ecdf_obj = ECDF(baseline_data_arr)
    scenario_ecdf_obj = ECDF(scenario_data_arr)
    KS_obj = ks_2samp(baseline_data_arr, scenario_data_arr)
    KS_stat = round(KS_obj.statistic, 4)
    baseline_trace = go.Scatter(x=np.around(baseline_ecdf_obj.x, decimals=1),
                                y=np.around(baseline_ecdf_obj.y, decimals=4),
                                mode='lines', name='Baseline')
    scenario_trace = go.Scatter(x=np.around(scenario_ecdf_obj.x, decimals=1),
                                y=np.around(scenario_ecdf_obj.y, decimals=4),
                                mode='lines',
                                name='{}'.format(scenarioid_jsdata))
    KS_annotation = [go.layout.Annotation(x=0, y=1.10,
                                          xref='paper', yref='paper',
                                          showarrow=False,
                                          text='Kolmogorov-Smirnov Distance: {}'.format(KS_stat))]
    xt = "{} in {}".format(var_name, unit_name)
    yt = "Fraction of Data"
    layout = go.Layout(autosize=True, width=600, height=375,
                       annotations=KS_annotation, legend_orientation="v",
                       xaxis=dict(title=dict(text=xt)),
                       yaxis=dict(title=dict(text=yt)))
    ecdf_fig = go.Figure(data=[baseline_trace, scenario_trace], layout=layout)
    graphJSON = json.dumps(ecdf_fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


def get_summary_table(runid, summary_range='default'):
    runid_query = (RunIdTable.objects
                   .filter(run_id=runid).values('id')[0].get('id'))

    hydrotable_query = (HydroTable.objects.filter(run_id=runid_query)
                        .values('variable', 'scenario',
                                'channel', 'unit',
                                'datetime', 'value'))
    hydrotable_df = pd.DataFrame.from_records(hydrotable_query)
    variable_searchers = list(hydrotable_df['variable'].unique())
    scenario_searchers = list(hydrotable_df['scenario'].unique())
    unit_searchers = list(hydrotable_df['unit'].unique())
    for v in variable_searchers:
        variable_query = (VariableTable.objects
                          .filter(id=v).values('variable')[0]
                          .get('variable'))
        hydrotable_df.variable.where(hydrotable_df.variable != v,
                                     variable_query,
                                     inplace=True)
    for s in scenario_searchers:
        scenario_query = (ScenarioTable.objects
                          .filter(id=s, run_id=runid_query)
                          .values('scenario')[0].get('scenario'))
        hydrotable_df.scenario.where(hydrotable_df.scenario != s,
                                     scenario_query, inplace=True)
    for u in unit_searchers:
        unit_query = (UnitTable.objects
                      .filter(id=u).values('unit')[0]
                      .get('unit'))
        hydrotable_df.unit.where(hydrotable_df.unit != u,
                                 unit_query, inplace=True)
    start_date = pd.to_datetime(runid.split("_")[-2],
                                yearfirst=True, format='%Y%m%d')
    if summary_range == 'default':
        end_date = pd.to_datetime(runid.split("_")[-1],
                                  yearfirst=True, format='%Y%m%d')
    elif summary_range == 'five':
        end_date = start_date + pd.Timedelta('5 days')
    elif summary_range == 'fourteen':
        end_date = start_date + pd.Timedelta('14 days')
    datetime_range = pd.date_range(start=start_date, end=end_date,
                                   freq='15T')
    selection = (hydrotable_df.loc[hydrotable_df['datetime']
                 .isin(datetime_range)])
    selection = selection[['variable', 'scenario', 'channel', 'datetime',
                           'value']]
    summary = selection.groupby(['variable', 'scenario', 'channel']).agg(
                                {'value': 'mean'})
    summary = summary.unstack(['variable', 'scenario'])
    summary.columns = summary.columns.droplevel()
    scenario_name_lst = (summary.columns.unique(level='scenario')
                         .values.tolist())
    omr_name_lst = [x for x in scenario_name_lst if 'OMR' in x]
    assert len(omr_name_lst) == 1
    omr_name = omr_name_lst[0]
    add_diff = summary.loc[:, pd.IndexSlice[:, omr_name]].sub(
                           summary.loc[:, pd.IndexSlice[:, 'Baseline']].values,
                           1).rename(columns={omr_name: 'Difference'})
    summary = summary.join(add_diff).sort_index(axis=1, level='variable',
                                                sort_remaining=False)
    summary = summary.rename(columns={'FLOW': 'Average Daily Flow (cfs)',
                                      'VEL': 'Average Daily Velocity (ft/s)'})
    summary = summary.round(2)
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
    tableJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return tableJSON


def get_channel_node_table(runid, variable='default'):
    runid_query = (RunIdTable.objects
                   .filter(run_id=runid).values('id')[0].get('id'))
    variable_query = (VariableTable.objects
                      .filter(variable=variable).values('id')[0].get('id'))
    hydrotable_query = (HydroTable.objects
                        .filter(run_id=runid_query, variable=variable_query)
                        .values('scenario', 'datetime', 'channel', 'value'))
    hydrotable_df = pd.DataFrame.from_records(hydrotable_query)
    scenario_searchers = list(hydrotable_df['scenario'].unique())
    for s in scenario_searchers:
        scenario_query = (ScenarioTable.objects
                          .filter(id=s, run_id=runid_query)
                          .values('scenario')[0].get('scenario'))
        hydrotable_df.scenario.where(hydrotable_df.scenario != s,
                                     scenario_query, inplace=True)
    print(hydrotable_df.head())
    # lists of the node numbers
    eight_nodes = ['CHAN012', 'CHAN049', 'CHAN050', 'CHAN094', 'CHAN124',
                   'CHAN148', 'CHAN422', 'CHAN423']
    first_nodes = ['CHAN012', 'CHAN049', 'CHAN050', 'CHAN094']
    second_nodes = ['CHAN124', 'CHAN148', 'CHAN422', 'CHAN423']
    start_date = pd.to_datetime(runid.split("_")[-2], yearfirst=True,
                                format='%Y%m%d')
    end_date = pd.to_datetime(runid.split("_")[-1], yearfirst=True,
                              format='%Y%m%d')
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

    trace1 = make_trace(first_df)
    trace2 = make_trace(second_df)
    layout = dict(autosize=False, width=1500, height=900)
    fig1 = go.Figure(data=[trace1], layout=layout)
    fig2 = go.Figure(data=[trace2], layout=layout)
    tableJSON1 = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
    tableJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    return tableJSON1, tableJSON2
