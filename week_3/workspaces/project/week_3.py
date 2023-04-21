from datetime import datetime
from typing import List
from operator import attrgetter

from dagster import (
    In,
    Nothing,
    OpExecutionContext,
    Out,
    ResourceDefinition,
    RetryPolicy,
    RunRequest,
    ScheduleDefinition,
    SensorEvaluationContext,
    SkipReason,
    graph,
    op,
    schedule,
    sensor,
    static_partitioned_config,
    String,
)
from workspaces.config import REDIS, S3
from workspaces.project.sensors import get_s3_keys
from workspaces.resources import mock_s3_resource, redis_resource, s3_resource
from workspaces.types import Aggregation, Stock


@op(
    config_schema={"s3_key": String},
    required_resource_keys={"s3"},
    out={"stocks": Out(dagster_type=List[Stock])},
    description="Get a list of stocks from an S3 file.",
    tags={"kind": "s3"},
)
def get_s3_data(context):
    s3_key = context.op_config["s3_key"]
    stock_data = context.resources.s3.get_data(key_name=s3_key)
    stocks = list(map(Stock.from_list, stock_data))
    context.log.info("Extracted stock list from S3")
    return stocks


@op(
    ins={"stocks": In(dagster_type=List[Stock])},
    out={"aggregation": Out(dagster_type=Aggregation)},
    description="Return the Aggregation with the highest stock price",
)
def process_data(context, stocks):
    highest_stock = max(stocks, key=attrgetter("high"))
    aggregation = Aggregation(date=highest_stock.date, high=highest_stock.high)
    context.log.info("Returned the highest performing stock as an Aggregation object")
    return aggregation


@op(
    required_resource_keys={"redis"},
    ins={"aggregation": In(dagster_type=Aggregation)},
    out=Out(Nothing),
    description="Upload an Aggregation to Redis",
    tags={"kind": "redis"},
)
def put_redis_data(context, aggregation):
    name = String(aggregation.date)
    value = String(aggregation.high)
    context.resources.redis.put_data(name=name, value=value)
    context.log.info("Aggregation loaded to redis cache")


@op(
    required_resource_keys={"s3"},
    ins={"aggregation": In(dagster_type=Aggregation)},
    out=Out(Nothing),
    description="Upload an Aggregation to S3",
    tags={"kind": "s3"},
)
def put_s3_data(context, aggregation):
    key_name = String(aggregation.date)
    context.resources.s3.put_data(key_name=key_name, data=aggregation)
    context.log.info("Aggregation loaded to S3")


@graph
def machine_learning_graph():
    stocks = get_s3_data()
    aggregation = process_data(stocks)
    put_redis_data(aggregation)
    put_s3_data(aggregation)


# Should the hardcoded s3_key values be replaced with S3?
local = {
    "ops": {
        "get_s3_data": {
            "config": {"s3_key": "prefix/stock_9.csv"},
        },
    },
}


docker = {
    "resources": {
        "s3": {"config": S3},
        "redis": {"config": REDIS},
    },
    "ops": {
        "get_s3_data": {
            "config": {"s3_key": "prefix/stock_9.csv"},
        },
    },
}


@static_partitioned_config(partition_keys=list(map(String, range(1, 11))))
def docker_config(partition_key: String):
    return {
        "resources": {
            "s3": {"config": S3},
            "redis": {"config": REDIS},
        },
        "ops": {
            "get_s3_data": {
                "config": {"s3_key": f"prefix/stock_{partition_key}.csv"},
            },
        },
    }


machine_learning_job_local = machine_learning_graph.to_job(
    name="machine_learning_job_local",
    config=local,
    resource_defs={"s3": mock_s3_resource, "redis": ResourceDefinition.mock_resource()},
)

machine_learning_job_docker = machine_learning_graph.to_job(
    name="machine_learning_job_docker",
    config=docker_config,
    resource_defs={
        "s3": s3_resource,
        "redis": redis_resource,
    },
    op_retry_policy=RetryPolicy(max_retries=10, delay=1),
)


# Run every 15 minutes
machine_learning_schedule_local = ScheduleDefinition(
    job=machine_learning_job_local,
    cron_schedule="*/15 * * * *",
)


# Run at the beginning of every hour
@schedule(job=machine_learning_job_docker, cron_schedule="0 * * * *")
def machine_learning_schedule_docker():
    ...


@sensor(job=machine_learning_job_docker, minimum_interval_seconds=30)
def machine_learning_sensor_docker(context):
    new_s3_keys = get_s3_keys(
        bucket="dagster",
        prefix="prefix",
        endpoint_url="http://localstack:4566",
    )
    if not new_s3_keys:
        yield SkipReason("No new s3 files found in bucket.")
        return
    for new_s3_key in new_s3_keys:
        yield RunRequest(
            run_key=new_s3_key,
            run_config={
                "resources": {
                    "s3": {"config": S3},
                    "redis": {"config": REDIS},
                },
                "ops": {
                    "get_s3_data": {
                        "config": {"s3_key": new_s3_key},
                    },
                },
            },
        )
