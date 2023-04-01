import csv
from datetime import datetime
from typing import Iterator, List

from dagster import (
    In,
    Nothing,
    OpExecutionContext,
    Out,
    String,
    job,
    op,
    usable_as_dagster_type,
)
from pydantic import BaseModel
from operator import attrgetter


@usable_as_dagster_type(description="Stock data")
class Stock(BaseModel):
    date: datetime
    close: float
    volume: int
    open: float
    high: float
    low: float

    @classmethod
    def from_list(cls, input_list: List[str]):
        """Do not worry about this class method for now"""
        return cls(
            date=datetime.strptime(input_list[0], "%Y/%m/%d"),
            close=float(input_list[1]),
            volume=int(float(input_list[2])),
            open=float(input_list[3]),
            high=float(input_list[4]),
            low=float(input_list[5]),
        )


@usable_as_dagster_type(description="Aggregation of stock data")
class Aggregation(BaseModel):
    date: datetime
    high: float


def csv_helper(file_name: str) -> Iterator[Stock]:
    with open(file_name) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            yield Stock.from_list(row)


@op(config_schema={"s3_key": String}, description="Get a list of stocks from an S3 file")
def get_s3_data_op(context) -> List[Stock]:
    s3_key = context.op_config["s3_key"]
    return list(csv_helper(s3_key))


@op(ins={"stocks": In(dagster_type=List[Stock], description="Return the Aggregation with the highest stock price")})
def process_data_op(context, stocks) -> Aggregation:
    highest_stock = max(stocks, key=attrgetter("high"))
    return Aggregation(date=highest_stock.date, high=highest_stock.high)
    

@op(ins={"aggregation": In(dagster_type=Aggregation, description="Upload an Aggregation to Redis")})
def put_redis_data_op(context, aggregation):
    pass


@op
def put_s3_data_op():
    pass


@job
def machine_learning_job():
    stocks = get_s3_data_op()
    aggregation = process_data_op(stocks)
    put_redis_data_op(aggregation)
    # put_s3_data_op()
