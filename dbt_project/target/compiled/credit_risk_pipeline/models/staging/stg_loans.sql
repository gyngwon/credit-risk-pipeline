with source as (
    select * from "credit_risk"."main"."raw_loans"
),

renamed as (
    select
        -- identifiers
        id as loan_id,
        member_id,

        -- loan amounts
        try_cast(loan_amnt as double) as loan_amount,
        try_cast(funded_amnt as double) as funded_amount,
        try_cast(funded_amnt_inv as double) as funded_amount_investors,
        try_cast(installment as double) as installment,

        -- loan terms
        try_cast(trim(replace(cast(term as varchar), 'months', '')) as integer) as term_months,
        try_cast(replace(cast(int_rate as varchar), '%', '') as double) as interest_rate,
        grade,
        sub_grade,
        purpose,
        title,

        -- borrower attributes
        emp_title as employer_title,
        emp_length as employment_length_raw,
        home_ownership,
        try_cast(annual_inc as double) as annual_income,
        verification_status,
        addr_state as state,
        zip_code,

        -- credit profile
        try_cast(dti as double) as dti,
        try_cast(delinq_2yrs as integer) as delinquencies_2yrs,
        try_strptime(earliest_cr_line, '%b-%Y') as earliest_credit_line_date,
        try_cast(inq_last_6mths as integer) as inquiries_last_6mths,
        try_cast(open_acc as integer) as open_accounts,
        try_cast(pub_rec as integer) as public_records,
        try_cast(pub_rec_bankruptcies as integer) as public_record_bankruptcies,
        try_cast(revol_bal as double) as revolving_balance,
        try_cast(replace(cast(revol_util as varchar), '%', '') as double) as revolving_utilization,
        try_cast(total_acc as integer) as total_accounts,
        

        -- loan status & performance
        loan_status,
        application_type,
        try_strptime(issue_d, '%b-%Y') as issue_date,
        try_cast(out_prncp as double) as outstanding_principal,
        try_cast(total_pymnt as double) as total_payment,
        try_cast(total_rec_prncp as double) as total_received_principal,
        try_cast(total_rec_int as double) as total_received_interest,
        try_cast(total_rec_late_fee as double) as total_received_late_fee,
        try_cast(recoveries as double) as recoveries,
        try_strptime(last_pymnt_d, '%b-%Y') as last_payment_date,
        try_cast(last_pymnt_amnt as double) as last_payment_amount,

        -- metadata
        _loaded_at

    from source
)

select * from renamed