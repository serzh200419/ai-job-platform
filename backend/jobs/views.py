from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Company, Job
from .serializers import CompanySerializer, JobListSerializer, JobSerializer


class JobListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobListSerializer

    def get_queryset(self):
        qs = Job.objects.filter(is_active=True).select_related("company").prefetch_related("skills")
        job_type = self.request.query_params.get("type")
        location = self.request.query_params.get("location")
        search = self.request.query_params.get("search")
        if job_type:
            qs = qs.filter(job_type=job_type)
        if location:
            qs = qs.filter(location__icontains=location)
        if search:
            qs = qs.filter(title__icontains=search)
        return qs


class JobDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer
    queryset = Job.objects.select_related("company").prefetch_related("skills")


class CompanyListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CompanySerializer
    queryset = Company.objects.all()
