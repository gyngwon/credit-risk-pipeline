with stg as (
    select * from {{ ref('stg_loans') }}
),

risk as (
    select * from {{ ref('int_borrower_risk_metrics') }}
),

credit_profile as (
    select
        {{ dbt_utils.generate_surrogate_key(['stg.loan_id']) }} as credit_profile_id,
        stg.loan_id,
        stg.grade,
        stg.sub_grade,
        risk.dti_bucket,
        risk.revolving_utilization_bucket,
        risk.credit_risk_tier

    from stg
    left join risk on stg.loan_id = risk.loan_id
)

select * from credit_profile