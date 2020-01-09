from django.db import models

# Create your models here.


class RunIdTable(models.Model):
    run_id = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True, editable=False,
                                   null=False, blank=False)
    last_modified = models.DateTimeField(auto_now=True, editable=False,
                                         null=False, blank=False)

    class Meta:
        ordering = ['created']


class VariableTable(models.Model):
    variable = models.CharField(max_length=50)


class ScenarioTable(models.Model):
    run_id = models.ForeignKey(RunIdTable, on_delete=models.CASCADE)
    scenario = models.CharField(max_length=50)


class UnitTable(models.Model):
    unit = models.CharField(max_length=10)


class HydroTable(models.Model):
    run_id = models.ForeignKey(RunIdTable, on_delete=models.CASCADE)
    path = models.CharField(max_length=200)
    variable = models.ForeignKey(VariableTable, on_delete=models.CASCADE)
    channel = models.CharField(max_length=50)
    scenario = models.ForeignKey(ScenarioTable, on_delete=models.CASCADE)
    unit = models.ForeignKey(UnitTable, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    value = models.FloatField()
    created = models.DateTimeField(auto_now_add=True, editable=False,
                                   null=False, blank=False)
    last_modified = models.DateTimeField(auto_now=True, editable=False,
                                         null=False, blank=False)


class VarSummaryTable(models.Model):
    run_id = models.ForeignKey(RunIdTable, on_delete=models.CASCADE)
    variable = models.ForeignKey(VariableTable, on_delete=models.CASCADE)
    scenario = models.ForeignKey(ScenarioTable, on_delete=models.CASCADE)
    channel = models.PositiveSmallIntegerField()
    mean = models.FloatField()
    std = models.FloatField()
    _min = models.FloatField()
    quant1 = models.FloatField()
    median = models.FloatField()
    quant3 = models.FloatField()
    _max = models.FloatField()
    created = models.DateTimeField(auto_now_add=True, editable=False,
                                   null=False, blank=False)
    last_modified = models.DateTimeField(auto_now=True, editable=False,
                                         null=False, blank=False)


class VarTotalTable(models.Model):
    run_id = models.ForeignKey(RunIdTable, on_delete=models.CASCADE)
    variable = models.ForeignKey(VariableTable, on_delete=models.CASCADE)
    scenario = models.ForeignKey(ScenarioTable, on_delete=models.CASCADE)
    channel = models.PositiveSmallIntegerField()
    datetime = models.DateTimeField()
    value = models.FloatField()
    created = models.DateTimeField(auto_now_add=True, editable=False,
                                   null=False, blank=False)
    last_modified = models.DateTimeField(auto_now=True, editable=False,
                                         null=False, blank=False)


class VarKSTable(models.Model):
    run_id = models.ForeignKey(RunIdTable, on_delete=models.CASCADE)
    variable = models.ForeignKey(VariableTable, on_delete=models.CASCADE)
    scenario0 = models.ForeignKey(ScenarioTable, on_delete=models.CASCADE,
                                  related_name='b')
    scenario1 = models.ForeignKey(ScenarioTable, on_delete=models.CASCADE,
                                  related_name='s')
    channel = models.PositiveSmallIntegerField()
    ks_stat = models.FloatField()
    created = models.DateTimeField(auto_now_add=True, editable=False,
                                   null=False, blank=False)
    last_modified = models.DateTimeField(auto_now=True, editable=False,
                                         null=False, blank=False)
