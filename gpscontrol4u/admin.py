from django.contrib import admin
from .models import Form, DataRecord, FormTemplate


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('form_name', 'user', 'language', 'is_predefined', 'is_active', 'created_at')
    list_filter = ('language', 'is_predefined', 'is_active', 'created_at')
    search_fields = ('form_name', 'user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'form_name', 'language')}),
        ('Form Structure', {'fields': ('form_structure',)}),
        ('Settings', {'fields': ('is_predefined', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(DataRecord)
class DataRecordAdmin(admin.ModelAdmin):
    list_display = ('form', 'user', 'language', 'submitted_at', 'latitude', 'longitude')
    list_filter = ('language', 'submitted_at', 'form__form_name')
    search_fields = ('user__email', 'form__form_name')
    raw_id_fields = ('user', 'form')
    readonly_fields = ('submitted_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'form', 'language')}),
        ('Data', {'fields': ('data_content',)}),
        ('Location', {'fields': ('latitude', 'longitude')}),
        ('Timestamps', {'fields': ('submitted_at', 'updated_at')}),
    )


@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'language', 'is_premium_only', 'is_active', 'created_at')
    list_filter = ('category', 'language', 'is_premium_only', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {'fields': ('name', 'description', 'category', 'language')}),
        ('Template Structure', {'fields': ('template_structure',)}),
        ('Access Control', {'fields': ('is_premium_only', 'is_active')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )
