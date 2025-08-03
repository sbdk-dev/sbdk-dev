{{
  config(
    materialized='view'
  )
}}

with source_data as (
    select * from {{ source('raw', 'raw_users') }}
),

cleaned as (
    select
        user_id,
        username,
        email,
        first_name,
        last_name,
        created_at,
        updated_at,
        country,
        city,
        subscription_tier,
        referrer,
        is_active,
        date_of_birth,
        phone,
        company,
        job_title,
        
        -- Calculated fields
        case 
            when date_of_birth is not null 
            then date_diff('year', date_of_birth, current_date)
            else null 
        end as age,
        
        case 
            when subscription_tier in ('premium', 'enterprise') then true
            else false 
        end as is_paid_subscriber,
        
        date_diff('day', created_at, current_date) as days_since_signup,
        
        -- Data quality flags
        case 
            when email is null or email = '' then false
            when first_name is null or first_name = '' then false  
            when last_name is null or last_name = '' then false
            else true 
        end as has_complete_profile
        
    from source_data
)

select * from cleaned