from django.core.management.base import BaseCommand, CommandError
from wiin.models import (RunIdTable, VariableTable, ScenarioTable, UnitTable,
                         HydroTable, VarSummaryTable, VarTotalTable, VarKSTable)
import os
import sys
import time
import pandas as pd



class Command(BaseCommand):
    help = 'Adds initial input data to the db.sqlite3 for testing. \
            Accepts one string arg for the tables_folder where the initial \
            datatables are located.'

    def add_arguments(self, parser):
        parser.add_argument('--tables_folder', type=str, help="Provide absolute \
                            folder pathname for the folder containing the \
                            initial input data tables in *.csv")

    def _fill_hydrotable(self, df):
        unique_run_id = df['run_id'].unique()[0]
        run_indx = RunIdTable.objects.get_or_create(run_id=unique_run_id)
        model_instances = []
        grouped_df = df.groupby(['path', 'variable', 'channel', 'scenario', 'unit'])
        for group_name, df_group in grouped_df:
            path_unique = df_group['path'].unique()
            assert len(path_unique) == 1
            var_unique = df_group['variable'].unique()
            assert len(var_unique) == 1
            channel_unique = df_group['channel'].unique()
            assert len(channel_unique) == 1
            scenario_unique = df_group['scenario'].unique()
            assert len(scenario_unique) == 1
            unit_unique = df_group['unit'].unique()
            assert len(unit_unique) == 1
            var_indx = VariableTable.objects.get_or_create(variable=var_unique[0])
            sce_indx = ScenarioTable.objects.get_or_create(scenario=scenario_unique[0], run_id=run_indx[0])
            uni_indx = UnitTable.objects.get_or_create(unit=unit_unique[0])
            for indx, row in df_group[['datetime', 'value']].iterrows():
                 model_instances.append(HydroTable(run_id=run_indx[0], path=path_unique[0], variable=var_indx[0], channel=channel_unique[0],
                                              scenario=sce_indx[0], unit=uni_indx[0], datetime=pd.to_datetime(row['datetime']),
                                              value=row['value']))
        print(len(model_instances))
        HydroTable.objects.bulk_create(model_instances, batch_size=10)
        print('Read and Write of HydroTable {} Complete'.format(unique_run_id))
        

    def _fill_varsummarytable(self, df):
        unique_run_id = df['run_id'].unique()[0]
        run_indx = RunIdTable.objects.get_or_create(run_id=unique_run_id)
        model_instances = []
        grouped_df = df.groupby(['variable', 'scenario'])
        for group_name, df_group in grouped_df:
            var_unique = df_group['variable'].unique()
            assert len(var_unique) == 1
            scenario_unique = df_group['scenario'].unique()
            assert len(scenario_unique) == 1
            var_indx = VariableTable.objects.get_or_create(variable=var_unique[0])
            sce_indx = ScenarioTable.objects.get_or_create(scenario=scenario_unique[0], run_id=run_indx[0])
            for indx, row in df_group.iterrows():
                model_instances.append(VarSummaryTable(run_id=run_indx[0], variable=var_indx[0], scenario=sce_indx[0],
                                                       channel=row['channel'], mean=row['mean'],
                                                       std=row['std'], _min=row['_min'], quant1=row['quant1'],
                                                       median=row['median'], quant3=row['quant3'], _max=row['_max']))
        print(len(model_instances))
        VarSummaryTable.objects.bulk_create(model_instances, batch_size=10)
        print('Read and Write of VarSummaryTable {} Complete'.format(unique_run_id))

    def _fill_vartotaltable(self, df):
        unique_run_id = df['run_id'].unique()[0]
        run_indx = RunIdTable.objects.get_or_create(run_id=unique_run_id)
        model_instances = []
        grouped_df = df.groupby(['variable', 'scenario', 'channel'])
        for group_name, df_group in grouped_df:
            var_unique = df_group['variable'].unique()
            assert len(var_unique) == 1
            scenario_unique = df_group['scenario'].unique()
            assert len(scenario_unique) == 1
            channel_unique = df_group['channel'].unique()
            assert len(channel_unique) == 1
            var_indx = VariableTable.objects.get_or_create(variable=var_unique[0])
            sce_indx = ScenarioTable.objects.get_or_create(scenario=scenario_unique[0], run_id=run_indx[0])
            for indx, row in df_group[['channel', 'datetime', 'value']].iterrows():
                model_instances.append(VarTotalTable(run_id=run_indx[0], variable=var_indx[0], scenario=sce_indx[0],
                                                     channel=channel_unique[0], datetime=pd.to_datetime(row['datetime']), value=row['value']))
        print(len(model_instances))
        VarTotalTable.objects.bulk_create(model_instances, batch_size=10)
        print('Read and Write of VarTotalTable {} Complete'.format(unique_run_id))
    
    def _fill_varkstable(self, df):
        unique_run_id = df['run_id'].unique()[0]
        run_indx = RunIdTable.objects.get_or_create(run_id=unique_run_id)
        model_instances = []
        grouped_df = df.groupby(['variable'])
        for group_name, df_group in grouped_df:
            print(group_name)
            var_indx = VariableTable.objects.get_or_create(variable=group_name)
            print(var_indx)
            print(var_indx[0])
            scenario0_unique = df_group['scenario0'].unique()
            assert len(scenario0_unique) == 1
            scenario1_unique = df_group['scenario1'].unique()
            assert len(scenario1_unique) == 1
            sce0_indx = ScenarioTable.objects.get_or_create(scenario=scenario0_unique[0], run_id=run_indx[0])
            sce1_indx = ScenarioTable.objects.get_or_create(scenario=scenario1_unique[0], run_id=run_indx[0])
            for indx, row in df_group[['channel', 'ks_stat']].iterrows():
                model_instances.append(VarKSTable(run_id=run_indx[0], variable=var_indx[0], scenario0=sce0_indx[0], scenario1=sce1_indx[0],
                                                  channel=row['channel'], ks_stat=row['ks_stat']))
        print(len(model_instances))
        VarKSTable.objects.bulk_create(model_instances, batch_size=10)
        print('Read and Write of VarKSTable {} Complete'.format(unique_run_id))

    def _fill_table(self, table_pathname, table_dict):
        determine_table = os.path.basename(table_pathname).split(".")[0]
        df = pd.read_csv(table_pathname, sep=",",
                         infer_datetime_format=True, parse_dates=True)
        unique_run_id = df['run_id'].unique()
        print(unique_run_id)
        print(unique_run_id[0])
        assert len(unique_run_id) == 1
        df.columns = [col.lower() for col in df.columns]
        table_dict.get(determine_table)(df)

    def handle(self, *args, **options):
        start = time.time()
        tables_folder = options['tables_folder']
        tables_folder_lst = [os.path.join(tables_folder, x)
                             for x in os.listdir(tables_folder)]
        table_dict = {"HydroTable": self._fill_hydrotable,
                      "VarSummary": self._fill_varsummarytable,
                      "VarTotal": self._fill_vartotaltable,
                      "VarKS": self._fill_varkstable}
        for i in tables_folder_lst:
            print(i)
            self._fill_table(i, table_dict)
        elapsed_time = time.time() - start
        print('Runtime: {} seconds'.format(round(elapsed_time, 5)))
