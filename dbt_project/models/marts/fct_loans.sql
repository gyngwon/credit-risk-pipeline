{{
    config(
        materialized='incremental',
        unique_key='loan_id'
    )
}}

with stg as (
    select * from {{ ref('stg_loans') }}
),

status_flags as (
    select * from {{ ref('int_loan_status_flags') }}
),

borrowers as (
    select loan_id, borrower_id from {{ ref('dim_borrowers') }}
),

credit_profile as (
    select loan_id, credit_profile_id from {{ ref('dim_credit_profile') }}
),

loan_product as (
    select loan_id, product_id from {{ ref('dim_loan_product') }}
),

final as (
    select
        stg.loan_id,
        borrowers.borrower_id,
        credit_profile.credit_profile_id,
        loan_product.product_id,
        stg.issue_date,

        -- measures
        stg.loan_amount,
        stg.funded_amount,
        stg.interest_rate,
        stg.installment,
        stg.outstanding_principal,
        stg.total_payment,
        stg.total_received_principal,
        stg.total_received_interest,
        stg.recoveries,

        -- risk flags
        status_flags.is_default,
        status_flags.is_fully_paid,
        status_flags.is_late,
        status_flags.is_current,
        status_flags.risk_status

    from stg
    left join status_flags on stg.loan_id = status_flags.loan_id
    left join borrowers on stg.loan_id = borrowers.loan_id
    left join credit_profile on stg.loan_id = credit_profile.loan_id
    left join loan_product on stg.loan_id = loan_product.loan_id
)

select * from final

{% if is_incremental() %}
where issue_date > (select max(issue_date) from {{ this }})
{% endif %}