from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns
from wiin import views

# create a router and register viewsets
router = SimpleRouter()
router.register(r'api/runid', views.RunIdViewSet)
router.register(r'api/variable', views.VariableViewSet)
router.register(r'api/scenario', views.ScenarioViewSet)
router.register(r'api/unit', views.UnitViewSet)
router.register(r'api/hydro', views.HydroViewSet)
router.register(r'api/vartotal', views.VarTotalViewSet)
router.register(r'api/varsummary', views.VarSummaryViewSet)
router.register(r'api/varks', views.VarKSViewSet)

# create urlpatterhsn for non-API routes
urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('summary_table/', views.FullSummaryView.as_view(),
         name='summary_table'),
    path('summary5_table/', views.Summary5View.as_view(),
         name='summary5_table'),
    path('summary14_table/', views.Summary14View.as_view(),
         name='summary14_table'),
    path('mfcn_table/', views.MfcnView.as_view(), name='mfcn_table'),
    path('mvcn_table/', views.MvcnView.as_view(), name='mvcn_table'),
]

urlpatterns += router.urls

urlpatterns = format_suffix_patterns(urlpatterns)
