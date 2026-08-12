-- This test FAILS if it returns any rows.
-- Funded amount should never exceed the requested loan amount.
select loan_id, loan_amount, funded_amount
from {{ ref('stg_loans') }}
where funded_amount > loan_amount