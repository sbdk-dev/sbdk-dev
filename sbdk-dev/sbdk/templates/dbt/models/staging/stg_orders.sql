{{
  config(
    materialized='view'
  )
}}

with source_data as (
    select * from {{ source('raw', 'raw_orders') }}
),

cleaned as (
    select
        order_id,
        user_id,
        order_number,
        created_at,
        completed_at,
        status,
        product_category,
        product_sku,
        quantity,
        unit_price,
        subtotal,
        discount_amount,
        discount_code,
        tax_amount,
        total_amount,
        currency,
        payment_method,
        payment_processor,
        billing_country,
        billing_state,
        billing_city,
        billing_postal_code,
        is_recurring,
        subscription_period,
        utm_source,
        utm_campaign,
        referral_code,
        customer_notes,
        shipping_required,
        shipping_cost,
        estimated_delivery,
        
        -- Calculated fields
        date(created_at) as order_date,
        extract(hour from created_at) as order_hour,
        extract(dow from created_at) as day_of_week,
        extract(month from created_at) as order_month,
        extract(year from created_at) as order_year,
        
        case 
            when completed_at is not null 
            then date_diff('hour', created_at, completed_at)
            else null 
        end as hours_to_completion,
        
        case 
            when discount_amount > 0 then true
            else false 
        end as has_discount,
        
        case 
            when discount_amount > 0 
            then round(discount_amount / subtotal * 100, 2)
            else 0 
        end as discount_percentage,
        
        case 
            when status = 'completed' then true
            else false 
        end as is_completed,
        
        case 
            when status in ('cancelled', 'refunded') then true
            else false 
        end as is_failed,
        
        case 
            when total_amount >= 100 then 'high_value'
            when total_amount >= 50 then 'medium_value'
            else 'low_value'
        end as order_value_tier,
        
        -- Payment categorization
        case 
            when payment_method in ('credit_card', 'stripe') then 'card'
            when payment_method in ('paypal', 'bank_transfer') then 'alternative'
            when payment_method = 'crypto' then 'crypto'
            else 'other'
        end as payment_category
        
    from source_data
    where created_at is not null
      and user_id is not null
      and total_amount > 0
)

select * from cleaned