{{
  config(
    materialized='view'
  )
}}

with source_data as (
    select * from {{ source('raw', 'raw_events') }}
),

cleaned as (
    select
        event_id,
        user_id,
        session_id,
        event_type,
        timestamp,
        utm_source,
        utm_medium,
        utm_campaign,
        page_url,
        referrer_url,
        user_agent,
        ip_address,
        country,
        device_type,
        browser,
        os,
        screen_resolution,
        is_mobile,
        duration_seconds,
        revenue,
        
        -- Calculated fields
        date(timestamp) as event_date,
        extract(hour from timestamp) as event_hour,
        extract(dow from timestamp) as day_of_week,
        
        case 
            when event_type in ('signup', 'purchase') then true
            else false 
        end as is_conversion_event,
        
        case 
            when utm_source in ('google', 'bing') then 'search'
            when utm_source in ('facebook', 'instagram', 'twitter', 'linkedin') then 'social'
            when utm_source = 'email' then 'email'
            when utm_source = 'direct' then 'direct'
            else 'other'
        end as traffic_category,
        
        -- Session indicators
        case 
            when session_id is not null then true
            else false 
        end as has_session_tracking,
        
        -- Revenue events
        case 
            when revenue > 0 then true
            else false 
        end as is_revenue_event
        
    from source_data
    where timestamp is not null
      and user_id is not null
      and event_type is not null
)

select * from cleaned