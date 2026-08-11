with stg as (
    select * from {{ ref('stg_loans') }}
),

employment as (
    select * from {{ ref('int_borrower_employment') }}
),

borrowers as (
    select
        {{ dbt_utils.generate_surrogate_key(['stg.loan_id']) }} as borrower_id,
        stg.loan_id,
        stg.state,
        stg.home_ownership,
        stg.verification_status,
        stg.annual_income,
        employment.employment_length_years,
        employment.employment_length_bucket

    from stg
    left join employment on stg.loan_id = employment.loan_id
)

select * from borrowers