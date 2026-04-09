from django.urls import path

from .views import LookupAPIView, LookupSSEView, LookupTemplateView

urlpatterns = [
    path("", LookupTemplateView.as_view(), name="lookup-template"),
    path("api/lookup/", LookupAPIView.as_view(), name="lookup"),
    path("sse/<str:job_id>/", LookupSSEView.as_view(), name="lookup-sse"),
]
