from azure_communication.azure_compute import get_aml_compute, get_conda_depencies, get_run_config
from azureml.core import Workspace, Datastore
from azureml.pipeline.core import PipelineData
from resources.local_helper_functions import copy_dependencies, load_env_variables
from azure_communication.pipelines import PipelineRegister

# Run this script to automatically set up the register/train/deploy pipeline on Azure


def copy_dataprep_dependencies():
    destination = 'azure_pipeline_steps/dataprep/'
    files = ['resources/sql.py', 'resources/helper_functions.py', 'azure_communication/azure_blob_storage.py']
    copy_dependencies(files, destination)


def copy_deploy_dependencies():
    destination = 'azure_pipeline_steps/deploy/server_files/'
    files = ['resources/sql.py', 'resources/projects.py']
    copy_dependencies(files, destination)


if __name__ == '__main__':
    ws = Workspace.from_config(path='./')
    print(ws)

    aml_compute = get_aml_compute(ws)
    conda_dep = get_conda_depencies()
    run_amlcompute = get_run_config(aml_compute, conda_dep)
    env_variables = load_env_variables()

    blob_datastore_name = 'workspaceblobstore'
    blob_store = Datastore(ws, blob_datastore_name)
    prepped_data_path = PipelineData('prepped_data', blob_store).as_dataset()

    pipeline_register = PipelineRegister(aml_compute, run_amlcompute, prepped_data_path, ws, env_variables)
    """ Copy only relevant dependencies to keep 'snapshot' folder small, this snapshot will be uploaded to Azure
    Files that already exist are overwritten """
    copy_dataprep_dependencies()
    copy_deploy_dependencies()

    dataprep_step = pipeline_register.setup_dataprep_step()
    automl_step = pipeline_register.setup_training_step()
    deploy_step = pipeline_register.setup_deploy_step()
    steps = [dataprep_step, automl_step, deploy_step]

    pipeline_register.create_pipeline(steps)
