with stg as (
    select * from {{ ref('stg_loans') }}
),

product as (
    select
        {{ dbt_utils.generate_surrogate_key(['loan_id']) }} as product_id,
        loan_id,
        term_months,
        purpose,
        title,
        application_type

    from stg
)

select * from product