from datetime import date
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

class ServiceRateCategoryQuerySet(models.QuerySet):
    def current_rates(self):
        today = date.today()
        return self.filter(start_date__lte=today, end_date__gte=today)
    
    def for_model(self, model_name):
        return self.filter(model_name=model_name)


class CurrentRatesManager(models.Manager):
    def get_queryset(self):
        return ServiceRateCategoryQuerySet(self.model, using=self._db)

    def current_rates(self):
        return self.get_queryset().current_rates()

    def for_model(self, model_name):
        return self.get_queryset().for_model(model_name)
    
    def monthly_rates(self):
        return self.current_rates().filter(cycle="month")
    
    def current_for_model(self, model_name):
        return self.current_rates().filter(model_name=model_name)


class ServiceRateCategory(TimeStampedModel):
    tier_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    model_display_name = models.CharField(max_length=255)
    model_description = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    rate = models.IntegerField()
    unit_rate = models.IntegerField()
    unit = models.CharField(max_length=255)
    cycle = models.CharField(max_length=255)

    objects = models.Manager()
    current = CurrentRatesManager()
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "service rate categories"
