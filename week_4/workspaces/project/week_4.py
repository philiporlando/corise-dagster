from datetime import datetime
from typing import List
from operator import attrgetter

from dagster import (
    AssetSelection,
    Nothing,
    OpExecutionContext,
    ScheduleDefinition,
    String,
    asset,
    define_asset_job,
    load_assets_from_current_module,
)
from workspaces.types import Aggregation, Stock
from workspaces.resources import mock_s3_resource, redis_resource, s3_resource


@asset(
    config_schema={"s3_key": String},
    required_resource_keys={"s3"},
    description="Get a list of stocks from an S3 file.",
    op_tags={"kind": "s3"},
)
def get_s3_data(context):
    s3_key = context.op_config["s3_key"]
    stock_data = context.resources.s3.get_data(key_name=s3_key)
    stocks = list(map(Stock.from_list, stock_data))
    context.log.info("Extracted stock list from S3")
    return stocks


@asset(
    description="Return the Aggregation with the highest stock price",
)
def process_data(context, get_s3_data):
    highest_stock = max(get_s3_data, key=attrgetter("high"))
    aggregation = Aggregation(date=highest_stock.date, high=highest_stock.high)
    context.log.info("Returned the highest performing stock as an Aggregation object")
    return aggregation


@asset(
    required_resource_keys={"redis"},
    description="Upload an Aggregation to Redis",
    op_tags={"kind": "redis"},
)
def put_redis_data(context, process_data):
    name = String(process_data.date)
    value = String(process_data.high)
    context.resources.redis.put_data(name=name, value=value)
    context.log.info("Aggregation loaded to redis cache")


@asset(
    required_resource_keys={"s3"},
    description="Upload an Aggregation to S3",
    op_tags={"kind": "s3"},
)
def put_s3_data(context, process_data):
    key_name = String(process_data.date)
    context.resources.s3.put_data(key_name=key_name, data=process_data)
    context.log.info("Aggregation loaded to S3")


project_assets = load_assets_from_current_module()


local_config = {
    "ops": {
        "get_s3_data": {
            "config": {"s3_key": "prefix/stock_9.csv"},
        },
    },
}

machine_learning_asset_job = define_asset_job(
    name="machine_learning_asset_job",
    # selection=project_assets,
    selection=AssetSelection.all(),
    config=local_config,
)

machine_learning_schedule = ScheduleDefinition(job=machine_learning_asset_job, cron_schedule="*/15 * * * *")
