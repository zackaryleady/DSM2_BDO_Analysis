from rest_framework import serializers
from wiin.models import (HydroTable, VarSummaryTable,
                         VarTotalTable, RunIdTable,
                         VariableTable, ScenarioTable,
                         UnitTable, VarKSTable)


class HydroTableSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = HydroTable
        fields = "__all__"


class VarSummarySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VarSummaryTable
        fields = "__all__"


class VarTotalSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VarTotalTable
        fields = "__all__"


class RunIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunIdTable
        fields = "__all__"


class VariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariableTable
        fields = "__all__"


class ScenarioSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ScenarioTable
        fields = "__all__"


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitTable
        fields = "__all__"


class VarKSSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VarKSTable
        fields = "__all__"
