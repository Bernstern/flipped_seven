import os

import boto3
import pytest
from moto import mock_aws


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ENDPOINT_URL", "")
    monkeypatch.setenv("BOTS_TABLE", "Flip7Bots")
    monkeypatch.setenv("RUNS_TABLE", "Flip7TournamentRuns")
    monkeypatch.setenv("TOKENS_TABLE", "Flip7Tokens")
    monkeypatch.setenv("BOT_TIMEOUT_SECONDS", "0.1")


@pytest.fixture
def dynamodb():
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        resource.create_table(
            TableName="Flip7Bots",
            KeySchema=[{"AttributeName": "bot_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "bot_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        resource.create_table(
            TableName="Flip7TournamentRuns",
            KeySchema=[{"AttributeName": "run_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "run_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        resource.create_table(
            TableName="Flip7Tokens",
            KeySchema=[{"AttributeName": "token_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "token_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield resource
