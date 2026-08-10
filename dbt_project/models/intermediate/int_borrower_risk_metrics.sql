with stg as (
    select * from {{ ref('stg_loans') }}
),

metrics as (
    select
        loan_id,
        grade,
        sub_grade,
        dti,
        revolving_utilization,

        -- LendingClub's own credit grade doubles as the risk tier here,
        -- since this dataset extract doesn't include FICO score columns
        case
            when grade in ('A', 'B') then 'low_risk'
            when grade in ('C', 'D') then 'moderate_risk'
            when grade in ('E', 'F', 'G') then 'high_risk'
            else 'unknown'
        end as credit_risk_tier,

        case
            when dti is null then 'unknown'
            when dti < 15 then 'low'
            when dti < 30 then 'moderate'
            when dti < 40 then 'high'
            else 'very_high'
        end as dti_bucket,

        case
            when revolving_utilization is null then 'unknown'
            when revolving_utilization < 30 then 'low'
            when revolving_utilization < 60 then 'moderate'
            else 'high'
        end as revolving_utilization_bucket

    from stg
)

select * from metrics