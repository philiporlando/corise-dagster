* running into issues with the Testing extension... it was working great at first, but now none of my tests are passing... I deleted a bunch of terminals and ran make week_2_tests. Now, the Testing extension is working again... maybe the debugger was stuck and I wasn't noticing?

* I'm not following how the local and docker dictionaries are being defined... specifically the docker dictionary. We are passing in the s3 and redis resources only for the docker job because we are using mock resources for the local job?

* Within the local to_job definition, I'm not understanding why we're using ResourceDefinition.mock_resource() instead of mock_s3_resource(). When I try to use this resource I get an error. This is despite the context parameter being included as an input param within its definition...?

E   dagster.core.errors.DagsterInvalidInvocationError: Resource initialization function has context argument, but no context was provided when invoking.

Correction: using mock_s3_resource (without the parens) is working for me...

* We are defining mock s3 and redis resources for our local deployment. From what I can tell, we're using the mock_s3_resource when materializing the get_s3_data() op, but it doesn't get used within the put_s3_data() op? This is despite the mock redis resource being used within the put_redis_data() op... The mock s3 resource appears to contain a list of stocks, but doesn't tell dagster how to interact with a mock s3 bucket? Is that correct? What am I missing here? 

* I was experimenting with being explicit about the missing input for the get_s3_data() op. When I try to set this to In(Nothing) I'm getting a cryptic error. Using a dictionary and setting an arbitrary "start" key is working... not sure if this is considered bad form though...

make week_2_tests:

E   dagster._check.ParameterCheckError: Param "ins" is not one of ['dict', 'frozendict']. Got In(dagster_type=<dagster.core.types.dagster_type._Nothing object at 0x7fcea8b883d0>, description=None, default_value=<class 'dagster.core.definitions.utils.NoValueSentinel'>, root_manager_key=None, metadata={}, asset_key=None, asset_partitions=None) which is type <class 'dagster.core.definitions.input.In'>.

Testing:

ERROR: not found: /workspace/corise-dagster/week_2/tests/test_answer.py::test_get_s3_data
(no name '/workspace/corise-dagster/week_2/tests/test_answer.py::test_get_s3_data' in any of [<Module test_answer.py>])


* I started my docker environment and tried running the machine_learning_job_docker within dagit. I'm getting the following error:

dagster._core.errors.DagsterExecutionStepExecutionError: Error occurred while executing op "get_s3_data":

  File "/opt/venv/lib/python3.8/site-packages/dagster/_core/execution/plan/execute_plan.py", line 268, in dagster_event_sequence_for_step
    for step_event in check.generator(step_events):
  File "/opt/venv/lib/python3.8/site-packages/dagster/_core/execution/plan/execute_step.py", line 375, in core_dagster_event_sequence_for_step
    for user_event in check.generator(
  File "/opt/venv/lib/python3.8/site-packages/dagster/_core/execution/plan/execute_step.py", line 91, in _step_output_error_checked_user_event_sequence
    for user_event in user_event_sequence:
  File "/opt/venv/lib/python3.8/site-packages/dagster/_core/execution/plan/compute.py", line 186, in execute_core_compute
    for step_output in _yield_compute_results(step_context, inputs, compute_fn):
  File "/opt/venv/lib/python3.8/site-packages/dagster/_core/execution/plan/compute.py", line 155, in _yield_compute_results
    for event in iterate_with_context(
  File "/opt/venv/lib/python3.8/site-packages/dagster/_utils/__init__.py", line 441, in iterate_with_context
    return
  File "/usr/local/lib/python3.8/contextlib.py", line 131, in __exit__
    self.gen.throw(type, value, traceback)
  File "/opt/venv/lib/python3.8/site-packages/dagster/_core/execution/plan/utils.py", line 84, in op_execution_error_boundary
    raise error_cls(

The above exception was caused by the following exception:
botocore.errorfactory.NoSuchBucket: An error occurred (NoSuchBucket) when calling the GetObject operation: The specified bucket does not exist

  File "/opt/venv/lib/python3.8/site-packages/dagster/_core/execution/plan/utils.py", line 54, in op_execution_error_boundary
    yield
  File "/opt/venv/lib/python3.8/site-packages/dagster/_utils/__init__.py", line 439, in iterate_with_context
    next_output = next(iterator)
  File "/opt/venv/lib/python3.8/site-packages/dagster/_core/execution/plan/compute_generator.py", line 122, in _coerce_solid_compute_fn_to_iterator
    result = invoke_compute_fn(
  File "/opt/venv/lib/python3.8/site-packages/dagster/_core/execution/plan/compute_generator.py", line 116, in invoke_compute_fn
    return fn(context, **args_to_pass) if context_arg_provided else fn(**args_to_pass)
  File "/opt/dagster/dagster_home/workspaces/project/week_2.py", line 33, in get_s3_data
    stocks = list(map(Stock.from_list, stocks))
  File "/opt/dagster/dagster_home/workspaces/resources.py", line 48, in get_data
    obj = self.client.get_object(Bucket=self.bucket, Key=key_name)
  File "/opt/venv/lib/python3.8/site-packages/botocore/client.py", line 530, in _api_call
    return self._make_api_call(operation_name, kwargs)
  File "/opt/venv/lib/python3.8/site-packages/botocore/client.py", line 960, in _make_api_call
    raise error_class(parsed_response, operation_name)



