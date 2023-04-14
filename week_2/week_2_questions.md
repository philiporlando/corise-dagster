* running into issues with the Testing extension... it was working great at first, but now none of my tests are passing... I deleted a bunch of terminals and ran make week_2_tests. Now, the Testing extension is working again... maybe the debugger was stuck and I wasn't noticing?

* I'm not following how the local and docker dictionaries are being defined... specifically the docker dictionary. We are passing in the s3 and redis resources only for the docker job because we are using mock resources for the local job?

* Within the local to_job definition, I'm not understanding why we're using ResourceDefinition.mock_resource() instead of mock_s3_resource(). When I try to use this resource I get an error. This is despite the context parameter being included as an input param within its definition...?

E   dagster.core.errors.DagsterInvalidInvocationError: Resource initialization function has context argument, but no context was provided when invoking.

* I was experimenting with being explicit about the missing input for the get_s3_data() op. When I try to set this to In(Nothing) I'm getting a cryptic error. Using a dictionary and setting an arbitrary "start" key is working... not sure if this is considered bad form though...

make week_2_tests:

E   dagster._check.ParameterCheckError: Param "ins" is not one of ['dict', 'frozendict']. Got In(dagster_type=<dagster.core.types.dagster_type._Nothing object at 0x7fcea8b883d0>, description=None, default_value=<class 'dagster.core.definitions.utils.NoValueSentinel'>, root_manager_key=None, metadata={}, asset_key=None, asset_partitions=None) which is type <class 'dagster.core.definitions.input.In'>.

Testing:

ERROR: not found: /workspace/corise-dagster/week_2/tests/test_answer.py::test_get_s3_data
(no name '/workspace/corise-dagster/week_2/tests/test_answer.py::test_get_s3_data' in any of [<Module test_answer.py>])





