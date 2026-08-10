with stg as (
    select * from {{ ref('stg_loans') }}
),

flagged as (
    select
        loan_id,
        loan_status,

        -- Terminal (resolved) vs. still-active loans.
        -- "Does not meet the credit policy" statuses are legacy LendingClub
        -- labels for loans that were later reclassified for policy reasons,
        -- but the underlying outcome (paid vs. charged off) is still valid,
        -- so they're folded into the same terminal buckets.
        case
            when loan_status in (
                'Fully Paid',
                'Does not meet the credit policy. Status:Fully Paid'
            ) then true
            else false
        end as is_fully_paid,

        case
            when loan_status in (
                'Charged Off',
                'Does not meet the credit policy. Status:Charged Off'
            ) then true
            else false
        end as is_default,

        case
            when loan_status in ('Late (31-120 days)', 'Late (16-30 days)') then true
            else false
        end as is_late,

        case
            when loan_status = 'In Grace Period' then true
            else false
        end as is_in_grace_period,

        case
            when loan_status = 'Current' then true
            else false
        end as is_current,

        -- A single top-level status used for grouping in the mart layer
        case
            when loan_status in (
                'Fully Paid',
                'Does not meet the credit policy. Status:Fully Paid'
            ) then 'paid'
            when loan_status in (
                'Charged Off',
                'Does not meet the credit policy. Status:Charged Off'
            ) then 'default'
            when loan_status in ('Late (31-120 days)', 'Late (16-30 days)') then 'late'
            when loan_status = 'In Grace Period' then 'grace_period'
            when loan_status = 'Current' then 'current'
            else 'unknown'
        end as risk_status

    from stg
)

select * from flagged