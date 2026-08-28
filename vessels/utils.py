from vessels.models import Vessel


def get_vessel_queryset():
    """Return a queryset of all vessels with prefetching for vessel images."""
    return Vessel.objects.prefetch_related('vessel_image').all()


def get_vessel_queryset_filtered_by_app_ref(app_refs):
    """Return a queryset of vessels filtered by app_ref with prefetching for vessel images."""
    return Vessel.objects.prefetch_related('vessel_image').filter(app_ref__in=app_refs)
