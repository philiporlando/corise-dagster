* define_asset_job() doesn't accept resource_defs as inputs... How are we using these resources then?
* it's not clear if we are creating local and docker jobs, or only docker?
* it's also not clear if we are supposed to use partitions and sensors this time?
* why are we defining project_assets? it doesn't seem to get used... I tried passing it to the selection parameter within define_asset_job() and got an error.