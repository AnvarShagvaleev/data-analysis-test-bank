import random
import pandas as pd
from datetime import timedelta, datetime, date


def generate_benefit_balances(
        number_of_clients: int,
        start_account_balance_date: str | date,
        end_account_balance_date: str | date,
        min_balance: int,
        max_balance: int,
        no_change_prob: float = 0.3
) -> pd.DataFrame:
    clients_list = _generate_unique_client_id(number_of_clients)
    dates_list = _generate_dates(start_account_balance_date, end_account_balance_date)

    balances_list = _generate_daily_start_account_balance(
        number_of_clients, dates_list, min_balance, max_balance, no_change_prob
    )

    data = []
    for client_idx, client in enumerate(clients_list):
        for date_idx, dt in enumerate(dates_list):
            data.append([client, dt, balances_list[client_idx][date_idx]])

    return pd.DataFrame(data, columns=["CODE", "BAL_DATE", "VALUE"])

def generate_benefit_points(
        benefit_balances: pd.DataFrame,
        max_transactions_per_day: int = 3,
        probability_of_mismatch: float = 0.1
) -> pd.DataFrame:
    data = []

    benefit_balances = benefit_balances.sort_values(by=["CODE", "BAL_DATE"]).reset_index(drop=True)

    for client_id in benefit_balances['CODE'].unique():
        client_balances = benefit_balances[benefit_balances['CODE'] == client_id].reset_index(drop=True)

        previous_balance = client_balances.loc[0, "VALUE"]

        for i in range(1, len(client_balances)):
            current_date = client_balances.loc[i, "BAL_DATE"]
            target_balance = client_balances.loc[i, "VALUE"]

            balance_difference = target_balance - previous_balance

            if balance_difference > 0:
                total_debit = random.randint(0, balance_difference)
                total_credit = balance_difference + total_debit
            elif balance_difference < 0:
                total_credit = random.randint(0, abs(balance_difference))
                total_debit = abs(balance_difference) + total_credit
            else:
                total_credit = 0
                total_debit = 0

            credits_list = _split_amount(total_credit, random.randint(1, max_transactions_per_day))
            debits_list = _split_amount(total_debit, random.randint(1, max_transactions_per_day))

            for credit in credits_list:
                data.append({
                    "CODE": client_id,
                    "DIRECTION": 1,
                    "CREATED_AT": _random_time_in_day(datetime.combine(current_date, datetime.min.time())),
                    "CUST_SUM": credit
                })

            for debit in debits_list:
                data.append({
                    "CODE": client_id,
                    "DIRECTION": 0,
                    "CREATED_AT": _random_time_in_day(datetime.combine(current_date, datetime.min.time())),
                    "CUST_SUM": debit
                })

            previous_balance = target_balance

            if random.random() < probability_of_mismatch:
                mismatch = random.randint(-100, 100)
                previous_balance += mismatch

    return pd.DataFrame(data, columns=["CODE", "DIRECTION", "CREATED_AT", "CUST_SUM"])

def generate_client_data(
        number_of_clients: int,
        start_open_date: str | datetime,
        end_open_date: str | datetime,
        operation_probability: float = 0.9
    ) -> pd.DataFrame:

    if isinstance(start_open_date, str):
        start_open_date = datetime.strptime(start_open_date, "%Y-%m-%d")

    if isinstance(end_open_date, str):
        end_open_date = datetime.strptime(end_open_date, "%Y-%m-%d")


    client_codes = _generate_unique_client_id(number_of_clients)

    total_days = (end_open_date - start_open_date).days
    open_dates = [start_open_date + timedelta(days=random.randint(0, total_days))
                  for _ in range(number_of_clients)]

    has_operations = [random.random() < operation_probability for _ in range(number_of_clients)]

    first_working_dates = []
    for open_date, has_op in zip(open_dates, has_operations):
        if has_op:
            days_since_open = random.randint(0, (end_open_date - open_date).days)
            first_working_date = open_date + timedelta(days=days_since_open)
            first_working_dates.append(first_working_date)
        else:
            first_working_dates.append(pd.NaT)

    clients_df = pd.DataFrame({
        'CODE': client_codes,
        'OPEN_DATE': open_dates,
        'FIRST_WORKING_DATE': first_working_dates
    })

    clients_df['OPEN_DATE'] = pd.to_datetime(clients_df['OPEN_DATE'])
    clients_df['FIRST_WORKING_DATE'] = pd.to_datetime(clients_df['FIRST_WORKING_DATE'])

    return clients_df

def _generate_unique_client_id(number_of_unique_clients: int) -> list[int]:
    unique_numbers = set()

    while len(unique_numbers) < number_of_unique_clients:
        number = random.randint(10_000_000, 99_999_999)
        unique_numbers.add(number)

    return list(unique_numbers)


def _generate_dates(start_date: str | date, end_date: str | date) -> list[date]:
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    number_of_days_between_dates = (end_date - start_date).days

    dates = [start_date + timedelta(days=i) for i in range(number_of_days_between_dates)]

    return dates


def _generate_daily_start_account_balance(
        number_of_clients: int,
        dates: list[date],
        min_balance: int,
        max_balance: int,
        no_change_prob: float = 0.3
) -> list[list[int]]:
    balances = []
    for _ in range(number_of_clients):
        client_balances = []
        previous_balance = random.randint(min_balance, max_balance)
        for _ in dates:
            if random.random() < no_change_prob:
                client_balances.append(previous_balance)
            else:
                previous_balance = random.randint(min_balance, max_balance)
                client_balances.append(previous_balance)
        balances.append(client_balances)
    return balances


def _split_amount(amount: int, num_splits: int) -> list[int]:
    if amount == 0:
        return [0] * num_splits
    splits = []
    for _ in range(num_splits - 1):
        part = random.randint(0, amount)
        splits.append(part)
        amount -= part
    splits.append(amount)
    return splits


def _random_time_in_day(date_obj: datetime) -> datetime:
    seconds_in_day = 60 * 60 * 24 - 1
    random_seconds = random.randint(0, seconds_in_day)
    return date_obj + timedelta(seconds=random_seconds)
