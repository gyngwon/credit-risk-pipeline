with stg as (
    select * from {{ ref('stg_loans') }}
),

parsed as (
    select
        loan_id,
        employment_length_raw,

        case
            when employment_length_raw = 'n/a' then null
            when employment_length_raw = '< 1 year' then 0
            when employment_length_raw = '10+ years' then 10
            else try_cast(
                regexp_extract(employment_length_raw, '(\d+)', 1) as integer
            )
        end as employment_length_years,

        -- Convenience bucket for grouping in dashboards
        case
            when employment_length_raw = 'n/a' then 'unknown'
            when employment_length_raw = '< 1 year' then '0-1 years'
            when try_cast(regexp_extract(employment_length_raw, '(\d+)', 1) as integer) <= 3
                then '1-3 years'
            when try_cast(regexp_extract(employment_length_raw, '(\d+)', 1) as integer) <= 6
                then '4-6 years'
            when employment_length_raw = '10+ years' then '10+ years'
            else '7-9 years'
        end as employment_length_bucket

    from stg
)

select * from parsed