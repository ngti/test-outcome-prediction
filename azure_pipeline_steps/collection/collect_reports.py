import json
from resources.helper_functions import get_file_number, load_aml_env_variables, create_blob_object, create_project_list, \
    load_projects


# Get latest project already in database
def collect_reports(projects, username, jenkins_key, temp_folder, azure_blob_storage):
    for project in projects:
        blobs_list = azure_blob_storage.list_blobs_for_project(project.jenkins_name)

        lowest = 0
        print("BLOB LIST:", blobs_list)
        filtered_blobs_list = [file for file in blobs_list if file.endswith('.json')]
        print("FILTERED:", filtered_blobs_list)
        for file in filtered_blobs_list:
            file_number = get_file_number(project.jenkins_name, file)
            if file_number > lowest:
                lowest = file_number

        highest = project.get_highest_build_number(username, jenkins_key)

        print("PROJECT: ", project.jenkins_name)
        print("LOWEST: ", lowest)
        print("HIGHEST: ", highest)
        for number in range(lowest+1, highest+1):
            build = project.get_build(number, username, jenkins_key)

            project_and_number = project.jenkins_name + '/' + str(number)
            file_name_info = project_and_number + 'INFO.json'
            file_name = project_and_number + '.json'

            with open(temp_folder + file_name_info, 'w') as outfile:
                json.dump(build, outfile, indent=4, separators=(',', ': '))

            azure_blob_storage.upload_blob(file_name_info)

            test_report = project.get_build_test_report(number, username, jenkins_key)
            if test_report:
                with open(temp_folder + file_name, 'w') as outfile:
                    json.dump(test_report, outfile, indent=4, separators=(',', ': '))
                azure_blob_storage.upload_blob(file_name)


if __name__ == '__main__':
    input_temp_folder = 'temp/'
    env_variables = load_aml_env_variables()

    used_projects = load_projects()
    jenkins_url = env_variables.get('jenkins_url')
    input_projects = create_project_list(used_projects, jenkins_url)

    azure_connection = env_variables.get('azure_connection')
    blob_container_name = env_variables.get('blob_container_name')
    input_azure_blob_storage = create_blob_object(input_temp_folder, azure_connection,
                                                  blob_container_name)

    collection_username = env_variables.get('username')
    collection_jenkins_key = env_variables.get('jenkins_key')
    collect_reports(input_projects, collection_username,
                    collection_jenkins_key, input_temp_folder,
                    input_azure_blob_storage)
