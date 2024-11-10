import pytest
from datetime import datetime, date
import pandas as pd
from generate_db_data import (_generate_unique_client_id, _generate_dates,
                              _generate_daily_start_account_balance, _split_amount,
                              generate_benefit_balances, generate_benefit_points,
                              generate_client_data)

def test_generate_unique_client_id():
    num_clients = 5
    client_ids = _generate_unique_client_id(num_clients)
    assert len(client_ids) == num_clients
    assert len(set(client_ids)) == num_clients
    for client_id in client_ids:
        assert 10_000_000 <= client_id <= 99_999_999

def test_generate_dates():
    start_date = "2024-01-01"
    end_date = "2024-01-10"
    dates = _generate_dates(start_date, end_date)
    assert len(dates) == 9
    assert dates[0] == date(2024, 1, 1)
    assert dates[-1] == date(2024, 1, 9)

def test_generate_daily_start_account_balance():
    dates = [date(2024, 1, i + 1) for i in range(5)]
    balances = _generate_daily_start_account_balance(
        number_of_clients=3,
        dates=dates,
        min_balance=100,
        max_balance=200,
        no_change_prob=0.5
    )
    assert len(balances) == 3
    for client_balances in balances:
        assert len(client_balances) == len(dates)
        for balance in client_balances:
            assert 100 <= balance <= 200

def test_generate_benefit_balances():
    df = generate_benefit_balances(
        number_of_clients=3,
        start_account_balance_date="2024-01-01",
        end_account_balance_date="2024-01-10",
        min_balance=100,
        max_balance=200
    )
    assert len(df) == 3 * 9  # 3 клиента * 9 дней
    assert list(df.columns) == ["CODE", "BAL_DATE", "VALUE"]

def test_split_amount():
    amount = 100
    num_splits = 5
    splits = _split_amount(amount, num_splits)
    assert len(splits) == num_splits
    assert sum(splits) == amount

def test_generate_benefit_points():
    benefit_balances = pd.DataFrame({
        "CODE": [1, 1, 2, 2],
        "BAL_DATE": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 1), date(2024, 1, 2)],
        "VALUE": [100, 150, 200, 250]
    })
    points_df = generate_benefit_points(benefit_balances, max_transactions_per_day=2)
    assert all(col in points_df.columns for col in ["CODE", "DIRECTION", "CREATED_AT", "CUST_SUM"])
    assert (points_df["DIRECTION"].isin([0, 1])).all()
    assert points_df["CUST_SUM"].ge(0).all()

def test_generate_client_data():
    df = generate_client_data(
        number_of_clients=3,
        start_open_date="2024-01-01",
        end_open_date="2024-01-31"
    )
    assert len(df) == 3
    assert "CODE" in df.columns and "OPEN_DATE" in df.columns and "FIRST_WORKING_DATE" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["OPEN_DATE"])
    assert pd.api.types.is_datetime64_any_dtype(df["FIRST_WORKING_DATE"])

