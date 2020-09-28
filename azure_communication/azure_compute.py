from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.core.environment import CondaDependencies
from azureml.core.runconfig import RunConfiguration


def get_aml_compute(workspace):
    # TODO: Set desired name for compute target
    aml_compute_target = "example_vm_name"
    try:
        aml_compute = AmlCompute(workspace, aml_compute_target)
        print("found existing compute target.")
    except ComputeTargetException:
        print("creating new compute target")

        # TODO: Configure desired VM, see: https://docs.microsoft.com/nl-nl/azure/virtual-machines/sizes-general
        provisioning_config = AmlCompute.provisioning_configuration(vm_size="STANDARD_D1_V2",
                                                                    min_nodes=0,
                                                                    max_nodes=1,
                                                                    vnet_resourcegroup_name="",
                                                                    vnet_name="-vn",
                                                                    subnet_name="default",
                                                                    idle_seconds_before_scaledown=1800,
                                                                    vm_priority='lowpriority')
        aml_compute = ComputeTarget.create(workspace, aml_compute_target, provisioning_config)
        aml_compute.wait_for_completion(show_output=True, min_node_count=None, timeout_in_minutes=20)
    print("Azure Machine Learning Compute attached")
    return aml_compute


def get_conda_depencies():
    conda_dep = CondaDependencies()
    conda_dep.set_python_version("3.6.2")

    with open('compute_pip_requirements.txt') as f:
        for requirement in f:
            conda_dep.add_pip_package(str(requirement))

    with open('compute_conda_requirements.txt') as f:
        for requirement in f:
            conda_dep.add_conda_package(str(requirement))

    return conda_dep


def get_run_config(aml_compute, conda_dep):
    run_amlcompute = RunConfiguration()
    run_amlcompute.target = aml_compute

    dockerfile = r"""
    FROM mcr.microsoft.com/azureml/base:intelmpi2018.3-ubuntu16.04

    RUN apt-get update && \
        apt-get install -y sudo curl apt-transport-https && \
        apt-get update && \
        sudo su && \
        curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
        curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
        sudo apt-get update && \
        sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
        sudo apt-get install -y unixodbc-dev
    """

    run_amlcompute.environment.docker.enabled = True
    run_amlcompute.environment.docker.base_image = None
    run_amlcompute.environment.docker.base_dockerfile = dockerfile
    run_amlcompute.environment.python.conda_dependencies = conda_dep

    return run_amlcompute
