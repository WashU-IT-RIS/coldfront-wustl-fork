from django.db import models
from model_utils.models import TimeStampedModel


class Service(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255)


class ServiceRateCategory(TimeStampedModel):
    service_id = models.ForeignKey(Service, on_delete=models.CASCADE)
    model_name = models.CharField(max_length=255)
    model_display_name = models.CharField(max_length=255)
    model_description = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()


class ServiceRateCategoryTier(TimeStampedModel):
    service_rate_category_id = models.ForeignKey(
        ServiceRateCategory, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    rate = models.IntegerField()
    unit_rate = models.IntegerField()
    unit = models.CharField(max_length=255)
    cycle = models.CharField(max_length=255)
