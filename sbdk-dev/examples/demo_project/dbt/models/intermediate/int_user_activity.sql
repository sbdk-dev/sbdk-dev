{{
  config(
    materialized='view'
  )
}}

with users as (
    select * from {{ ref('stg_users') }}
),

events as (
    select * from {{ ref('stg_events') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

user_events as (
    select
        user_id,
        count(*) as total_events,
        count(*) filter (where event_type = 'page_view') as pageviews,
        count(*) filter (where event_type = 'click') as clicks,
        count(*) filter (where event_type = 'signup') as signups,
        count(*) filter (where event_type = 'login') as logins,
        count(*) filter (where event_type = 'purchase') as purchase_events,
        count(*) filter (where is_conversion_event = true) as conversion_events,
        count(*) filter (where is_revenue_event = true) as revenue_events,
        coalesce(sum(revenue), 0) as total_event_revenue,
        coalesce(sum(duration_seconds), 0) as total_time_on_site,
        count(distinct session_id) filter (where session_id is not null) as unique_sessions,
        count(distinct event_date) as active_days,
        min(timestamp) as first_event_at,
        max(timestamp) as last_event_at,
        count(distinct traffic_category) as traffic_sources_used
    from events
    group by user_id
),

user_orders as (
    select
        user_id,
        count(*) as total_orders,
        count(*) filter (where is_completed = true) as completed_orders,
        count(*) filter (where is_failed = true) as failed_orders,
        count(*) filter (where is_recurring = true) as recurring_orders,
        coalesce(sum(total_amount) filter (where is_completed = true), 0) as total_order_revenue,
        coalesce(avg(total_amount) filter (where is_completed = true), 0) as avg_order_value,
        coalesce(sum(discount_amount), 0) as total_discounts_used,
        count(distinct product_category) as product_categories_purchased,
        min(created_at) as first_order_at,
        max(created_at) as last_order_at,
        count(distinct payment_method) as payment_methods_used
    from orders
    group by user_id
),

combined as (
    select
        u.user_id,
        u.username,
        u.email,
        u.first_name,
        u.last_name,
        u.created_at as user_created_at,
        u.country,
        u.city,
        u.subscription_tier,
        u.referrer,
        u.is_active,
        u.age,
        u.is_paid_subscriber,
        u.days_since_signup,
        u.has_complete_profile,
        
        -- Event metrics
        coalesce(e.total_events, 0) as total_events,
        coalesce(e.pageviews, 0) as pageviews,
        coalesce(e.clicks, 0) as clicks,
        coalesce(e.signups, 0) as signups,
        coalesce(e.logins, 0) as logins,
        coalesce(e.purchase_events, 0) as purchase_events,
        coalesce(e.conversion_events, 0) as conversion_events,
        coalesce(e.revenue_events, 0) as revenue_events,
        coalesce(e.total_event_revenue, 0) as total_event_revenue,
        coalesce(e.total_time_on_site, 0) as total_time_on_site,
        coalesce(e.unique_sessions, 0) as unique_sessions,
        coalesce(e.active_days, 0) as active_days,
        e.first_event_at,
        e.last_event_at,
        coalesce(e.traffic_sources_used, 0) as traffic_sources_used,
        
        -- Order metrics
        coalesce(o.total_orders, 0) as total_orders,
        coalesce(o.completed_orders, 0) as completed_orders,
        coalesce(o.failed_orders, 0) as failed_orders,
        coalesce(o.recurring_orders, 0) as recurring_orders,
        coalesce(o.total_order_revenue, 0) as total_order_revenue,
        coalesce(o.avg_order_value, 0) as avg_order_value,
        coalesce(o.total_discounts_used, 0) as total_discounts_used,
        coalesce(o.product_categories_purchased, 0) as product_categories_purchased,
        o.first_order_at,
        o.last_order_at,
        coalesce(o.payment_methods_used, 0) as payment_methods_used,
        
        -- Calculated metrics
        case 
            when e.pageviews > 0 and o.completed_orders > 0 
            then round(o.completed_orders::float / e.pageviews * 100, 2)
            else 0 
        end as purchase_conversion_rate,
        
        case 
            when e.total_events > 0 
            then round(e.conversion_events::float / e.total_events * 100, 2)
            else 0 
        end as event_conversion_rate,
        
        case 
            when e.unique_sessions > 0 
            then round(e.total_events::float / e.unique_sessions, 2)
            else 0 
        end as events_per_session,
        
        case 
            when u.days_since_signup > 0 and e.active_days > 0
            then round(e.active_days::float / u.days_since_signup * 100, 2)
            else 0 
        end as activity_frequency_percentage,
        
        -- Total combined revenue
        coalesce(e.total_event_revenue, 0) + coalesce(o.total_order_revenue, 0) as total_revenue,
        
        -- User activity classification
        case 
            when o.completed_orders > 0 then 'customer'
            when e.signups > 0 then 'signed_up'
            when e.total_events > 10 then 'engaged_visitor'
            when e.total_events > 0 then 'visitor'
            else 'inactive'
        end as user_type
        
    from users u
    left join user_events e on u.user_id = e.user_id
    left join user_orders o on u.user_id = o.user_id
)

select * from combined