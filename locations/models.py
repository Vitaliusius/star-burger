from django.db import models


class Location(models.Model):
    address = models.CharField(
        'Адрес',
        max_length=200,
        unique=True,
    )
    lon = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Долгота',
    )
    lat = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Широта',
    )
    request_date = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'

    def __str__(self):
        return self.address
