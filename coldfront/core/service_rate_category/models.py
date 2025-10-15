from datetime import date
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords


class CurrentRatesManager(models.Manager):
    def get_queryset(self):
        today = date.today()
        return super.get_queryset(self).filter(start_date__gt=today, end_date__lt=today)


class Service(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255)

    history = HistoricalRecords()


class ServiceRateCategory(TimeStampedModel):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    model_name = models.CharField(max_length=255)
    model_display_name = models.CharField(max_length=255)
    model_description = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    objects = models.Manager()
    current = CurrentRatesManager()
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "service rate categories"


class ServiceRateCategoryTier(TimeStampedModel):
    service_rate_category = models.ForeignKey(
        ServiceRateCategory, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    rate = models.IntegerField()
    unit_rate = models.IntegerField()
    unit = models.CharField(max_length=255)
    cycle = models.CharField(max_length=255)

    history = HistoricalRecords()
