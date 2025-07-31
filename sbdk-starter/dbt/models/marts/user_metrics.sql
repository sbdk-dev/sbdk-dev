{{
  config(
    materialized='table'
  )
}}

with user_activity as (
    select * from {{ ref('int_user_activity') }}
),

final as (
    select
        user_id,
        username,
        email,
        first_name,
        last_name,
        user_created_at,
        country,
        city,
        subscription_tier,
        referrer,
        is_active,
        age,
        is_paid_subscriber,
        days_since_signup,
        has_complete_profile,
        
        -- Engagement metrics
        total_events,
        pageviews,
        clicks,
        logins,
        unique_sessions,
        active_days,
        traffic_sources_used,
        events_per_session,
        activity_frequency_percentage,
        total_time_on_site,
        
        -- Conversion metrics
        signups,
        purchase_events,
        conversion_events,
        purchase_conversion_rate,
        event_conversion_rate,
        
        -- Revenue metrics
        total_orders,
        completed_orders,
        failed_orders,
        recurring_orders,
        total_order_revenue,
        total_event_revenue,
        total_revenue,
        avg_order_value,
        total_discounts_used,
        product_categories_purchased,
        payment_methods_used,
        
        -- Timing metrics
        first_event_at,
        last_event_at,
        first_order_at,
        last_order_at,
        
        -- User classification
        user_type,
        
        -- Customer lifetime value estimate
        case 
            when recurring_orders > 0 and days_since_signup > 0
            then round(total_revenue * (365.0 / days_since_signup) * 2, 2)  -- Rough 2-year CLV estimate
            else total_revenue 
        end as estimated_clv,
        
        -- Engagement score (0-100)
        least(100, 
            (case when active_days > 0 then least(25, active_days) else 0 end) +
            (case when unique_sessions > 0 then least(25, unique_sessions) else 0 end) +
            (case when total_events > 0 then least(25, least(25, total_events / 10)) else 0 end) +
            (case when completed_orders > 0 then 25 else 0 end)
        ) as engagement_score,
        
        -- Risk classification
        case 
            when last_event_at < current_date - interval '90 days' and total_orders > 0 then 'churn_risk'
            when last_event_at < current_date - interval '30 days' and user_type = 'customer' then 'at_risk'
            when activity_frequency_percentage < 10 and days_since_signup > 30 then 'low_engagement'
            when user_type = 'customer' and recurring_orders = 0 then 'one_time_buyer'
            when user_type = 'customer' and recurring_orders > 0 then 'loyal_customer'
            when user_type = 'engaged_visitor' then 'potential_customer'
            else 'standard'
        end as risk_category,
        
        -- Value tier
        case 
            when total_revenue >= 1000 then 'high_value'
            when total_revenue >= 500 then 'medium_value'
            when total_revenue >= 100 then 'low_value'
            when total_revenue > 0 then 'minimal_value'
            else 'no_value'
        end as value_tier,
        
        -- Recency, Frequency, Monetary (RFM) components
        case 
            when last_order_at >= current_date - interval '30 days' then 5
            when last_order_at >= current_date - interval '60 days' then 4
            when last_order_at >= current_date - interval '90 days' then 3
            when last_order_at >= current_date - interval '180 days' then 2
            when last_order_at is not null then 1
            else 0
        end as recency_score,
        
        case 
            when completed_orders >= 10 then 5
            when completed_orders >= 5 then 4
            when completed_orders >= 3 then 3
            when completed_orders >= 2 then 2
            when completed_orders >= 1 then 1
            else 0
        end as frequency_score,
        
        case 
            when total_revenue >= 1000 then 5
            when total_revenue >= 500 then 4
            when total_revenue >= 200 then 3
            when total_revenue >= 50 then 2
            when total_revenue > 0 then 1
            else 0
        end as monetary_score,
        
        -- Data freshness
        current_timestamp as updated_at
        
    from user_activity
)

select * from final