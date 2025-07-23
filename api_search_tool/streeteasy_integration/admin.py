from django.contrib import admin
from django.utils.html import format_html
from .models import StreetEasyProperty, StreetEasySearch, StreetEasyAPIKey, StreetEasyLiquidityEvent, StreetEasyEntity


@admin.register(StreetEasyProperty)
class StreetEasyPropertyAdmin(admin.ModelAdmin):
    list_display = [
        'street_easy_id', 'address', 'neighborhood', 'property_type', 
        'formatted_price_display', 'bedrooms', 'bathrooms', 'status', 'last_scraped'
    ]
    list_filter = [
        'property_type', 'status', 'neighborhood', 'borough', 
        'bedrooms', 'parking', 'doorman', 'elevator', 'last_scraped'
    ]
    search_fields = ['address', 'neighborhood', 'borough', 'street_easy_id']
    readonly_fields = ['street_easy_id', 'created_at', 'updated_at', 'last_scraped']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('street_easy_id', 'property_type', 'status')
        }),
        ('Location', {
            'fields': ('address', 'neighborhood', 'borough', 'zipcode', 'latitude', 'longitude')
        }),
        ('Property Details', {
            'fields': ('price', 'bedrooms', 'bathrooms', 'square_feet', 'unit_type')
        }),
        ('Building Information', {
            'fields': ('building_name', 'building_type', 'year_built')
        }),
        ('Features', {
            'fields': ('amenities', 'pet_policy', 'parking', 'doorman', 'elevator')
        }),
        ('Listing Information', {
            'fields': ('agent_name', 'agent_company', 'listing_url', 'image_urls')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_scraped', 'raw_data'),
            'classes': ('collapse',)
        })
    )
    
    def formatted_price_display(self, obj):
        return obj.formatted_price
    formatted_price_display.short_description = 'Price'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    actions = ['update_property_details', 'mark_as_expired']
    
    def update_property_details(self, request, queryset):
        """Action to update property details by re-scraping"""
        from .scraper import StreetEasyScraper
        scraper = StreetEasyScraper()
        updated_count = 0
        
        for property_obj in queryset:
            if property_obj.listing_url:
                try:
                    details = scraper.get_property_details(property_obj.listing_url)
                    for key, value in details.items():
                        if hasattr(property_obj, key) and value:
                            setattr(property_obj, key, value)
                    property_obj.save()
                    updated_count += 1
                except Exception:
                    continue
        
        self.message_user(request, f'Updated {updated_count} properties.')
    update_property_details.short_description = 'Update property details'
    
    def mark_as_expired(self, request, queryset):
        """Mark properties as expired"""
        updated = queryset.update(status='expired')
        self.message_user(request, f'Marked {updated} properties as expired.')
    mark_as_expired.short_description = 'Mark as expired'


@admin.register(StreetEasySearch)
class StreetEasySearchAdmin(admin.ModelAdmin):
    list_display = [
        'search_id', 'property_type', 'neighborhood', 'price_range_display', 
        'bedroom_range_display', 'results_count', 'last_executed'
    ]
    list_filter = ['property_type', 'neighborhood', 'last_executed']
    search_fields = ['search_id', 'neighborhood']
    readonly_fields = ['search_id', 'created_at', 'last_executed']
    
    fieldsets = (
        ('Search Information', {
            'fields': ('search_id', 'search_parameters', 'results_count')
        }),
        ('Search Filters', {
            'fields': ('property_type', 'neighborhood', 'min_price', 'max_price', 
                      'min_bedrooms', 'max_bedrooms')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_executed')
        })
    )
    
    def price_range_display(self, obj):
        if obj.min_price and obj.max_price:
            return f"${obj.min_price:,.0f} - ${obj.max_price:,.0f}"
        elif obj.min_price:
            return f"${obj.min_price:,.0f}+"
        elif obj.max_price:
            return f"Under ${obj.max_price:,.0f}"
        return "Any price"
    price_range_display.short_description = 'Price Range'
    
    def bedroom_range_display(self, obj):
        if obj.min_bedrooms is not None and obj.max_bedrooms is not None:
            if obj.min_bedrooms == obj.max_bedrooms:
                return f"{obj.min_bedrooms} BR"
            return f"{obj.min_bedrooms}-{obj.max_bedrooms} BR"
        elif obj.min_bedrooms is not None:
            return f"{obj.min_bedrooms}+ BR"
        elif obj.max_bedrooms is not None:
            return f"Up to {obj.max_bedrooms} BR"
        return "Any bedrooms"
    bedroom_range_display.short_description = 'Bedrooms'
    
    actions = ['re_run_search']
    
    def re_run_search(self, request, queryset):
        """Re-run selected searches"""
        from .scraper import StreetEasyAgent
        agent = StreetEasyAgent()
        
        for search in queryset:
            try:
                search_params = search.search_parameters
                if search.property_type == 'sale':
                    properties = agent.search_sales(**search_params)
                else:
                    properties = agent.search_rentals(**search_params)
                
                search.results_count = len(properties)
                search.save()
            except Exception:
                continue
        
        self.message_user(request, f'Re-ran {queryset.count()} searches.')
    re_run_search.short_description = 'Re-run search'


@admin.register(StreetEasyAPIKey)
class StreetEasyAPIKeyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'is_active', 'rate_limit_per_hour', 
        'requests_made_today', 'last_request_time'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('API Key Information', {
            'fields': ('name', 'api_key', 'is_active')
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_per_hour', 'requests_made_today', 'last_request_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    actions = ['reset_daily_requests']
    
    def reset_daily_requests(self, request, queryset):
        """Reset daily request counters"""
        updated = queryset.update(requests_made_today=0)
        self.message_user(request, f'Reset request counters for {updated} API keys.')
    reset_daily_requests.short_description = 'Reset daily requests'


@admin.register(StreetEasyLiquidityEvent)
class StreetEasyLiquidityEventAdmin(admin.ModelAdmin):
    list_display = [
        'event_id', 'seller_name', 'buyer_name', 'formatted_amount_display', 
        'event_type', 'transaction_date', 'property_address', 'confidence_score'
    ]
    list_filter = [
        'event_type', 'seller_type', 'buyer_type', 'transaction_date', 
        'neighborhood', 'borough', 'confidence_score'
    ]
    search_fields = ['seller_name', 'buyer_name', 'property_address', 'event_id']
    readonly_fields = ['event_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_id', 'event_type', 'transaction_date', 'transaction_amount', 'currency')
        }),
        ('Parties Involved', {
            'fields': ('seller_name', 'seller_type', 'buyer_name', 'buyer_type')
        }),
        ('Property Details', {
            'fields': ('property_address', 'neighborhood', 'borough', 'property_type', 
                      'square_footage', 'unit_count', 'price_per_sqft', 'cap_rate')
        }),
        ('Transaction Details', {
            'fields': ('broker_firm', 'broker_name')
        }),
        ('Source Information', {
            'fields': ('source_url', 'source_publication', 'confidence_score')
        }),
        ('Additional Data', {
            'fields': ('notes', 'tags', 'raw_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def formatted_amount_display(self, obj):
        return obj.formatted_amount
    formatted_amount_display.short_description = 'Amount'
    
    actions = ['update_entity_metrics']
    
    def update_entity_metrics(self, request, queryset):
        """Update metrics for entities involved in selected events"""
        from .liquidity_scraper import LiquidityEventScraper
        scraper = LiquidityEventScraper()
        
        for event in queryset:
            scraper._update_entities_from_event(event.to_dict())
        
        self.message_user(request, f'Updated entity metrics for {queryset.count()} events.')
    update_entity_metrics.short_description = 'Update entity metrics'


@admin.register(StreetEasyEntity)
class StreetEasyEntityAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'entity_type', 'transaction_count', 'formatted_total_volume', 
        'formatted_largest_transaction', 'last_transaction_date'
    ]
    list_filter = ['entity_type', 'most_active_year', 'last_transaction_date']
    search_fields = ['name', 'description']
    readonly_fields = ['entity_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Entity Information', {
            'fields': ('entity_id', 'name', 'entity_type', 'description')
        }),
        ('Details', {
            'fields': ('headquarters_location', 'founded_year', 'website')
        }),
        ('Transaction Metrics', {
            'fields': ('total_transaction_volume', 'transaction_count', 'largest_transaction', 
                      'avg_transaction_size', 'last_transaction_date', 'most_active_year')
        }),
        ('Market Focus', {
            'fields': ('primary_markets', 'property_types_focus')
        }),
        ('Additional Data', {
            'fields': ('aliases', 'related_entities', 'tags'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def formatted_total_volume(self, obj):
        volume = float(obj.total_transaction_volume)
        if volume >= 1_000_000_000:
            return f"${volume/1_000_000_000:.1f}B"
        elif volume >= 1_000_000:
            return f"${volume/1_000_000:.1f}M"
        else:
            return f"${volume:,.0f}"
    formatted_total_volume.short_description = 'Total Volume'
    
    def formatted_largest_transaction(self, obj):
        if obj.largest_transaction:
            amount = float(obj.largest_transaction)
            if amount >= 1_000_000_000:
                return f"${amount/1_000_000_000:.1f}B"
            elif amount >= 1_000_000:
                return f"${amount/1_000_000:.1f}M"
            else:
                return f"${amount:,.0f}"
        return "N/A"
    formatted_largest_transaction.short_description = 'Largest Transaction'
    
    actions = ['refresh_metrics']
    
    def refresh_metrics(self, request, queryset):
        """Refresh transaction metrics for selected entities"""
        for entity in queryset:
            entity.update_metrics()
        
        self.message_user(request, f'Refreshed metrics for {queryset.count()} entities.')
    refresh_metrics.short_description = 'Refresh metrics'


# Customize admin site
admin.site.site_header = "StreetEasy Integration Admin"
admin.site.site_title = "StreetEasy Admin"
admin.site.index_title = "StreetEasy Integration Administration"