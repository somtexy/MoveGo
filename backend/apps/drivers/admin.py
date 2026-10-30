from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.urls import reverse
from .models import DriverProfile


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'plate_number', 'review_status', 'is_online', 'updated_at')
    list_filter = ('review_status', 'is_online')
    search_fields = ('user__username', 'full_name', 'plate_number', 'license_number')
    readonly_fields = ('user', 'full_name', 'first_name', 'last_name', 'nin', 'license_number',
                       'vehicle_make', 'vehicle_model', 'vehicle_color', 'plate_number',
                       'document_links', 'is_online', 'created_at', 'updated_at')
    fields = ('user', 'full_name', 'first_name', 'last_name', 'nin', 'license_number',
              'vehicle_make', 'vehicle_model', 'vehicle_color', 'plate_number',
              'document_links', 'review_status', 'is_online', 'created_at', 'updated_at')

    @admin.display(description='Private verification photos')
    def document_links(self, obj):
        if not obj.pk:
            return 'Available after submission'
        labels = [('nin_document', 'NIN document'), ('license_photo', 'Driver licence'),
                  ('selfie_photo', 'Selfie')]
        links = []
        for kind, label in labels:
            if getattr(obj, kind):
                url = reverse('driver-review-document', args=[obj.pk, kind])
                links.append(format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', url, label))
        return format_html('{}', format_html_join(' | ', '{}', ((link,) for link in links))) if links else 'Not uploaded (older application)'

    def save_model(self, request, obj, form, change):
        if obj.review_status != DriverProfile.Review.APPROVED:
            obj.is_online = False
        super().save_model(request, obj, form, change)
