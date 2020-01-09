from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View, FormView

from rest_framework.viewsets import ModelViewSet

from wiin.models import (HydroTable, VarSummaryTable, VarTotalTable,
                         RunIdTable, VariableTable, ScenarioTable,
                         UnitTable, VarKSTable)
from wiin.serializers import (HydroTableSerializer, VarSummarySerializer,
                              VarTotalSerializer, RunIdSerializer,
                              VariableSerializer, ScenarioSerializer,
                              UnitSerializer, VarKSSerializer)

from wiin.utils import (get_mapgraph, get_mapKS, get_summary_table,
                        get_channel_node_table)

import json
import requests

# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class HomePageView(View):

    def get(self, request):
        context_dict = {}
        runid_call = requests.get("http://127.0.0.1:8000/api/runid/")
        scenario_call = requests.get("http://127.0.0.1:8000/api/scenario")
        variable_call = requests.get("http://127.0.0.1:8000/api/variable")
        runid_json = runid_call.json()
        scenario_json = scenario_call.json()
        variable_json = variable_call.json()
        context_dict['run_id'] = json.dumps([x['run_id'] for x in runid_json])
        scen_runid = None
        for x in scenario_json:
            if not x['scenario'] == 'Baseline':
                scen_runid = requests.get(x['run_id']).json().get("run_id")
        context_dict['scenario_id'] = json.dumps([{'scenario': x['scenario'],
                                                   'run_id': scen_runid}])
        variable_id_lst = []
        for x in variable_json:
            y = x['variable']
            if y not in variable_id_lst:
                variable_id_lst.append(y)
        context_dict['variable_id'] = json.dumps(variable_id_lst)
        print(context_dict)
        return render(request, 'mapvis.html',
                      context=context_dict,
                      status=200)

    def post(self, request):
        runid_jsdata = request.POST.get('myRun', '')
        scenarioid_jsdata = request.POST.get('myScenario', '')
        variableid_jsdata = request.POST.get('myVariable', '')
        channelid_jsdata = request.POST.get('myChannel', '')
        figobj = get_mapgraph(runid_jsdata, scenarioid_jsdata,
                              variableid_jsdata, channelid_jsdata)
        ks = get_mapKS(runid_jsdata, scenarioid_jsdata,
                       variableid_jsdata, channelid_jsdata)
        return JsonResponse([figobj, ks], safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class FullSummaryView(View):

    def get(self, request):
        context_dict = {}
        run_id_call = requests.get("http://127.0.0.1:8000/api/runid/")
        run_id_json = run_id_call.json()
        context_dict['run_id'] = json.dumps([x['run_id'] for x in run_id_json])
        return render(request, 'fullsum.html',
                      context=context_dict,
                      status=200)

    def post(self, request):
        runid_jsdata = request.POST.get('myRun', '')
        tableJSON = get_summary_table(runid_jsdata, summary_range='default')
        return JsonResponse(tableJSON, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class Summary5View(View):

    def get(self, request):
        context_dict = {}
        run_id_call = requests.get("http://127.0.0.1:8000/api/runid/")
        run_id_json = run_id_call.json()
        context_dict['run_id'] = json.dumps([x['run_id'] for x in run_id_json])
        return render(request, 'fivesum.html',
                      context=context_dict,
                      status=200)

    def post(self, request):
        runid_jsdata = request.POST.get('myRun', '')
        tableJSON = get_summary_table(runid_jsdata, summary_range='five')
        return JsonResponse(tableJSON, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class Summary14View(View):

    def get(self, request):
        context_dict = {}
        run_id_call = requests.get("http://127.0.0.1:8000/api/runid/")
        run_id_json = run_id_call.json()
        context_dict['run_id'] = json.dumps([x['run_id'] for x in run_id_json])
        return render(request, 'fourteensum.html',
                      context=context_dict,
                      status=200)

    def post(self, request):
        runid_jsdata = request.POST.get('myRun', '')
        tableJSON = get_summary_table(runid_jsdata, summary_range='fourteen')
        return JsonResponse(tableJSON, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class MfcnView(View):

    def get(self, request):
        context_dict = {}
        run_id_call = requests.get("http://127.0.0.1:8000/api/runid/")
        run_id_json = run_id_call.json()
        context_dict['run_id'] = json.dumps([x['run_id'] for x in run_id_json])
        return render(request, 'daily_flow.html',
                      context=context_dict,
                      status=200)

    def post(self, request):
        runid_jsdata = request.POST.get('myRun', '')
        tableJSON1, tableJSON2 = get_channel_node_table(runid_jsdata,
                                                        variable='FLOW')
        return JsonResponse([tableJSON1, tableJSON2], safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class MvcnView(FormView):
    def get(self, request):
        context_dict = {}
        run_id_call = requests.get("http://127.0.0.1:8000/api/runid/")
        run_id_json = run_id_call.json()
        context_dict['run_id'] = json.dumps([x['run_id'] for x in run_id_json])
        return render(request, 'daily_vel.html',
                      context=context_dict,
                      status=200)

    def post(self, request):
        runid_jsdata = request.POST.get('myRun', '')
        tableJSON1, tableJSON2 = get_channel_node_table(runid_jsdata,
                                                        variable='VEL')
        return JsonResponse([tableJSON1, tableJSON2], safe=False)


class RunIdViewSet(ModelViewSet):
    queryset = RunIdTable.objects.all()
    serializer_class = RunIdSerializer


class VariableViewSet(ModelViewSet):
    queryset = VariableTable.objects.all()
    serializer_class = VariableSerializer


class ScenarioViewSet(ModelViewSet):
    queryset = ScenarioTable.objects.all()
    serializer_class = ScenarioSerializer


class UnitViewSet(ModelViewSet):
    queryset = UnitTable.objects.all()
    serializer_class = UnitSerializer


class HydroViewSet(ModelViewSet):
    queryset = HydroTable.objects.all()
    serializer_class = HydroTableSerializer


class VarTotalViewSet(ModelViewSet):
    queryset = VarTotalTable.objects.all()
    serializer_class = VarTotalSerializer


class VarSummaryViewSet(ModelViewSet):
    queryset = VarSummaryTable.objects.all()
    serializer_class = VarSummarySerializer


class VarKSViewSet(ModelViewSet):
    queryset = VarKSTable.objects.all()
    serializer_class = VarKSSerializer
