from azure_communication.azure_compute import get_aml_compute, get_conda_depencies, get_run_config
from azureml.core import Workspace
from resources.local_helper_functions import copy_dependencies, load_env_variables
from azure_communication.pipelines import PipelineCollection


def copy_collection_dependencies():
    destination = 'azure_pipeline_steps/collection/'
    files = ['resources/projects.py', 'resources/helper_functions.py', 'azure_communication/azure_blob_storage.py',
             'resources/projects.json']
    copy_dependencies(files, destination)


def copy_preprocess_dependencies():
    destination = 'azure_pipeline_steps/preprocessing/'
    files = ['resources/projects.py', 'resources/helper_functions.py', 'resources/sql.py',
             'azure_communication/prediction.py', 'azure_communication/azure_blob_storage.py',
             'resources/projects.json']
    copy_dependencies(files, destination)


if __name__ == '__main__':
    ws = Workspace.from_config(path='./')

    aml_compute = get_aml_compute(ws)
    conda_dep = get_conda_depencies()
    run_amlcompute = get_run_config(aml_compute, conda_dep)
    env_variables = load_env_variables()

    pipeline_collection = PipelineCollection(aml_compute, run_amlcompute, ws, env_variables)
    """ Copy only relevant dependencies to keep 'snapshot' folder small, this snapshot will be uploaded to Azure
    Files that already exist are overwritten """
    copy_collection_dependencies()
    copy_preprocess_dependencies()

    data_collection_step = pipeline_collection.setup_data_collection_step()
    preprocessing_step = pipeline_collection.setup_preprocessing_step()

    steps = [data_collection_step, preprocessing_step]
    collection_pipeline = pipeline_collection.create_pipeline(steps)
