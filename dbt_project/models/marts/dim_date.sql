with stg as (
    select distinct issue_date from {{ ref('stg_loans') }}
    where issue_date is not null
),

dates as (
    select
        issue_date as date_day,
        extract(year from issue_date) as year,
        extract(month from issue_date) as month,
        extract(quarter from issue_date) as quarter,
        strftime(issue_date, '%B') as month_name,
        strftime(issue_date, '%Y-%m') as year_month

    from stg
)

select * from dates