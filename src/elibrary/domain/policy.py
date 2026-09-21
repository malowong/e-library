from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LendingPolicy:
    max_active_loans: int = 5
    loan_period_days: int = 14
