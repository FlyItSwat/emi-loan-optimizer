"""Loan amortization and prepayment models. Currency units are arbitrary (INR in UI)."""
from dataclasses import dataclass

@dataclass
class LoanResult:
    rows: list[dict]
    total_interest: float
    total_paid: float
    months: int
    emi: float

def emi(principal: float, annual_rate: float, years: int) -> float:
    if principal <= 0 or annual_rate < 0 or not 1 <= years <= 40:
        raise ValueError('Principal must be positive, rate nonnegative, and term 1–40 years')
    n = years * 12
    r = annual_rate / 1200
    if r == 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** -n)

def amortize(principal: float, annual_rate: float, years: int,
             monthly_extra: float = 0, one_time_extra: float = 0,
             one_time_month: int = 1, mode: str = 'reduce_term') -> LoanResult:
    if monthly_extra < 0 or one_time_extra < 0 or not 1 <= one_time_month <= years * 12:
        raise ValueError('Prepayments must be nonnegative; month must fall within term')
    if mode not in ('reduce_term', 'reduce_emi'):
        raise ValueError('Unknown prepayment mode')
    payment = emi(principal, annual_rate, years)
    original_payment = payment
    balance = float(principal)
    rate = annual_rate / 1200
    rows = []
    total_interest = 0.0
    total_paid = 0.0
    for month in range(1, years * 12 + 1):
        if balance <= 1e-8:
            break
        interest = balance * rate
        regular = min(payment, balance + interest)
        principal_regular = max(0.0, regular - interest)
        extra = min(max(0.0, balance - principal_regular), monthly_extra + (one_time_extra if month == one_time_month else 0))
        balance = max(0.0, balance - principal_regular - extra)
        if balance < 1e-8:
            balance = 0.0
        total_interest += interest
        total_paid += regular + extra
        rows.append({'month': month, 'emi_payment': regular, 'interest': interest,
                     'principal': principal_regular, 'prepayment': extra,
                     'total_payment': regular + extra, 'balance': balance,
                     'cumulative_interest': total_interest})
        if mode == 'reduce_emi' and balance > 1e-8 and extra > 0:
            remaining = years * 12 - month
            if remaining:
                if rate == 0:
                    payment = balance / remaining
                else:
                    payment = balance * rate / (1 - (1 + rate) ** -remaining)
    return LoanResult(rows, total_interest, total_paid, len(rows), original_payment)
