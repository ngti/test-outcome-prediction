import shutil
import pathlib
import configparser


def copy_dependencies(files, destination):
    absolute_path = str(pathlib.Path(__file__).parent.absolute()) + '/'
    destination = destination
    for file in files:
        shutil.copyfile(absolute_path + file, absolute_path + destination + file)


def load_env_variables():
    config = configparser.ConfigParser()
    absolute_path = str(pathlib.Path(__file__).parent.absolute()) + '/'
    config.read(absolute_path + 'config.ini')

    env_variables = {'username': config['GIT']['GitEmail'],
                     'git_repos_url': config['GIT']['GitReposUrl'],
                     'git_api_key': config['GIT']['GitAPIKey'],
                     'jenkins_url': config['JENKINS']['JenkinsUrl'],
                     'jenkins_key': config['JENKINS']['JenkinsAPIKey'],
                     'azure_connection': config['AZURE']['AzureConnection'],
                     'score_endpoint': config['AZURE']['ScoreEndpoint'],
                     'score_endpoint_key': config['AZURE']['ScoreEndpointAPIKey'],
                     'blob_container_name': config['AZURE']['BlobContainerName'],
                     'sql_server': config['SQL']['Server'],
                     'sql_database': config['SQL']['Database'],
                     'sql_username': config['SQL']['Username'],
                     'sql_password': config['SQL']['Password']}
    return env_variables
