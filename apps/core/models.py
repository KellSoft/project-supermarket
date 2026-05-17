from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base: created_at + updated_at on every model."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(TimeStampedModel):
    """Extends TimeStampedModel with soft-delete support."""

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self):
        super().delete()

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
