import os
import json
from azure_communication.azure_blob_storage import AzureBlobStorage
from resources.projects import Project


def create_project_list(projects, jenkins_url):
    project_list = []
    for project in projects:
        project_list.append(Project(project['jenkins_name'], project['github_name'], jenkins_url))

    return project_list


def load_projects():
    with open('../projects.json') as f:
        projects = json.loads(f)

    return projects


def get_file_number(project_name, found_file):
    found_file_number = found_file.replace('INFO', '')
    found_file_number = found_file_number.strip(project_name + '/').strip('.json')
    return int(found_file_number)


def load_aml_env_variables():
    env_variables = {'username': os.getenv('AML_PARAMETER_username'),
                     'git_repos_url': os.getenv('AML_PARAMETER_git_repos_url'),
                     'git_api_key': os.getenv('AML_PARAMETER_git_api_key'),
                     'jenkins_url': os.getenv('AML_PARAMETER_jenkins_url'),
                     'jenkins_key': os.getenv('AML_PARAMETER_jenkins_key'),
                     'azure_connection': os.getenv('AML_PARAMETER_azure_connection'),
                     'score_endpoint': os.getenv('AML_PARAMETER_score_endpoint'),
                     'score_endpoint_key': os.getenv('AML_PARAMETER_score_endpoint_key'),
                     'blob_container_name': os.getenv('AML_PARAMETER_blob_container_name'),
                     'sql_server': os.getenv('AML_PARAMETER_sql_server'),
                     'sql_database': os.getenv('AML_PARAMETER_sql_database'),
                     'sql_username': os.getenv('AML_PARAMETER_sql_username'),
                     'sql_password': os.getenv('AML_PARAMETER_sql_password')}
    return env_variables


def create_blob_object(temp_folder, azure_connection, blob_container):
    return AzureBlobStorage(blob_container, temp_folder, azure_connection)
