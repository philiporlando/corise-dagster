* Why do the local config dicts use "prefix/stock_9.csv" instead of "data/stock_9.csv"? 

Ok, I'm realizing that this is how localstack is being configured.

* Should the bucket, prefix, and endpoint_url params within the machine_learning_sensor_docker definition be passed in as config, or hardcoded? I'm struggling to see how they can be passed in via config... context.op_config seems wrong... 

Brien mentioned that schedules are not configureable via the context parameter, so this is the only way to do this.

* What should the body of the machine_learning_schedule_docker definition look like? I ran a test without defining anything and it worked after defining the schedule decorator... 

The function body should have something in there! We need to loop through each partition key and yield a RunRequest. Briend will share a walkthrough of this later on slack. Something similar to 

for partition_key in docker_config.get_partition_keys():
  yield RunRequest(run_key=partition_key, run_config=docker_config.get_run_config(partition_key))

* Why should we use build_schedule_from_partitioned_job instead of our sensor function definition?

Brien mentioned that this approach can only be used for time-based partitions, not static ones...

* Why are we defining the static docker config dictionary if we are only using the docker_config() function?

Brien mentioned that the static docker config dictionary is not required by the pipeline...
It was just there as a source of inspiration when defining docker_config()

* It's not clear how I should be launching a run of the machine_learning_job_docker job. Dagit is prompting me to scaffold missing config when launching manually, and then fails because the default config is invalid. I set the cron schedule to every minute as a workaround. 

Brien confirmed that this missing scaffolding occurs because we are passing in the run config to the sensors/schedules, but dagit doesn't know what config to use when using the launchpad. There is an option in the top-right corner of the launchpad window that can be explored if you want to scaffold this config manually.

* What should the workflow be to add a stock_11.csv file and observe the new partition running in dagit? make restart_project does not seem to be working... I've already updated the local_stack.sh to copy this new file over to the endpoint.

Brien walked me through this in detail over the call. We do not need to modify the static partition key list(range(1, 11)). That is a separate config from the sensor's run config, which dynamically determines how many new files were added to the s3 bucket (prefix). 

Instead, he had me launch docker, and then jump inside an interactive terminal for our localstack instance via docker exect -it {localstack pid}. From there, I ran `aws --endpoint-url=$ENDPOINT_URL s3 cp data/stock_11.csv s3://dagster/prefix/stock_11.csv`, which loaded the new file into our s3 bucket. I then watched the sensor via dagit and, sure enough, it picked up the 11th file and ran a new job. The remaining 10 partitions were skipped because they had already ran previously!