-- Interest rates outside 0-40% are almost certainly data errors
select loan_id, interest_rate
from {{ ref('stg_loans') }}
where interest_rate < 0 or interest_rate > 40