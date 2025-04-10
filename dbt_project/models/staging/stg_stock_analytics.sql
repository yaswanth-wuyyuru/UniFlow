with source as (
    select * from {{source('RAW', 'STOCK_ANALYTICS')}}
),

renamed as (
    select
    symbol,
    price,
    target_high,
    target_low,
    target_mean,
    recommendation,
    analyst_count,
    fetched_at::timestamp_ntz as fetched_at
    from source 
)

select * from renamed