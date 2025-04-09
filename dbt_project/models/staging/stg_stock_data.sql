
SELECT
    symbol,
    DATE(timestamp) AS trade_date,
    open,
    high,
    low,
    close,
    volume
FROM {{ source('raw', 'stock_data') }}
