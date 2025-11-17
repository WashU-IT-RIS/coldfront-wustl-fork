from datetime import date
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords


class ServiceRateCategoryQuerySet(models.QuerySet):
    def for_date(self, usage_date: date) -> models.QuerySet:
        return self.filter(start_date__lte=usage_date, end_date__gte=usage_date)

    def for_model(self, model_name: str) -> models.QuerySet:
        return self.filter(model_name=model_name)

    def for_tier(self, tier_name: str) -> models.QuerySet:
        return self.filter(tier_name=tier_name)

    def for_cycle(self, cycle: str) -> models.QuerySet:
        return self.filter(cycle=cycle)


class ServiceRateCategory(TimeStampedModel):
    tier_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    model_display_name = models.CharField(max_length=255, null=True, blank=True)
    model_description = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    unit_rate = models.IntegerField()
    unit = models.CharField(max_length=255)
    cycle = models.CharField(max_length=255)

    objects = models.Manager()
    rates = ServiceRateCategoryQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "service rate categories"

    def __str__(self) -> str:
        return f"{self.model_name} - {self.tier_name} - {self.cycle} ({self.start_date} to {self.end_date})"
