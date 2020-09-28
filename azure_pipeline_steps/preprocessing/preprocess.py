import os
import json
from resources.projects import BuildData
from resources.helper_functions import load_aml_env_variables, create_blob_object, create_project_list, load_projects
from resources.sql import SQLConnection
from azure_communication.prediction import predict_and_archive_file


def preprocess(projects, temp_folder, column_list, sql_conn, azure_blob_storage, preprocess_env_variables):
    for project in projects:
        azure_blob_storage.download_blobs_to_local_temp_folder(project.jenkins_name)

        json_files = [json_file for json_file in os.listdir(temp_folder + '/' + project.jenkins_name + '/')
                      if json_file.endswith('INFO.json')]

        for json_file in json_files:
            print('PROJECT:', project.jenkins_name)
            print('OPENING FILE:', json_file)
            with open(temp_folder + '/' + project.jenkins_name + '/' + json_file) as f:
                json_data = json.load(f)

            build_data = BuildData(project.jenkins_name, project.github_name, json_file, json_data,
                                   column_list, env_variables)

            print('TEST RESULT:', build_data.real_result)
            if build_data.real_result not in ['SUCCESS', 'FAILURE']:
                print('NO TEST RESULT, SKIPPING...')
                continue

            row_list = build_data.create_row_list()

            if row_list:
                print('BULK INSERTING ROWS...')
                sql_conn.insert_row_into_sql(row_list)
            else:
                print('NO ROWS TO ADD, SKIPPING...')

            prediction_endpoint = preprocess_env_variables.get('score_endpoint')
            score_endpoint_key = preprocess_env_variables.get('score_endpoint_key')
            predict_and_archive_file(build_data.build_number, project.github_name, project.jenkins_name,
                                     prediction_endpoint, score_endpoint_key, azure_blob_storage, json_file)

        azure_blob_storage.delete_blobs_from_local_temp_folder(project.jenkins_name)

    print('PREPROCESSING COMPLETED')


if __name__ == '__main__':
    input_temp_folder = 'temp'
    env_variables = load_aml_env_variables()

    env_jenkins_url = env_variables.get('jenkins_url')

    used_projects = load_projects()
    input_projects = create_project_list(used_projects, env_jenkins_url)
    input_sql_conn = SQLConnection(env_variables)

    azure_connection = env_variables.get('azure_connection')
    blob_container_name = env_variables.get('blob_container_name')
    input_azure_blob_storage = create_blob_object(input_temp_folder, azure_connection, blob_container_name)

    with input_sql_conn:
        input_column_list = input_sql_conn.list_sql_column_names()

        preprocess(input_projects, input_temp_folder, input_column_list, input_sql_conn, input_azure_blob_storage,
                   env_variables)
