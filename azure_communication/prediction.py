import requests


def predict_and_archive_file(build_number, github_name, jenkins_name, prediction_endpoint, score_endpoint_key,
                             azure_blob_storage, json_file):

    print("PREDICT AND ARCHIVE FILE:", json_file)
    request_prediction(build_number, github_name, jenkins_name,
                       prediction_endpoint, score_endpoint_key)

    azure_blob_storage.delete_blob_from_main_storage(jenkins_name, json_file)
    azure_blob_storage.upload_blob_to_archive(jenkins_name, json_file)


def request_prediction(build_number, github_name, jenkins_name, prediction_url, endpoint_key):
    headers = {'Authorization': 'Bearer ' + endpoint_key,
               'Content-Type': 'application/json'}
    r = requests.post(prediction_url,
                      json={"build": str(build_number),
                            "project": github_name,
                            "jenkins": jenkins_name},
                      headers=headers)
    print("PREDICTION RESPONSE CODE:", r)
    print("PREDICTION RESPONSE:", r.content)
