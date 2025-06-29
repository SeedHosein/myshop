from django.db import models

# Create your models here.

class CorePermissions(models.Model):
    """
    This model defines custom permissions for the application.
    It is used to create a permission 'view_dashboard' which allows users to view the dashboard home page.
    """

    class Meta:
        managed = False  # No database table created for this model
        permissions = [
            ("view_dashboard", "Can view the dashboard home page"),
            ("view_data", "Can view the data in the dashboard"),
        ]

class SiteVisit(models.Model):
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Total Site Visits: {self.count}"

    @classmethod
    def get_instance(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def increment_visit_count(cls):
        visit = cls.get_instance()
        visit.count += 1
        visit.save(update_fields=['count'])
        return visit.count
