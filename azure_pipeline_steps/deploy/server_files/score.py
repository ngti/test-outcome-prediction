import json
import numpy as np
import os
import pandas as pd
from dotenv import load_dotenv
from sklearn.externals import joblib
from azureml.core import Model
from pathlib import Path
from inference_schema.schema_decorators import input_schema, output_schema
from inference_schema.parameter_types.numpy_parameter_type import NumpyParameterType
from inference_schema.parameter_types.pandas_parameter_type import PandasParameterType
from server_files.projects import Project, BuildData
from server_files.sql import SQLConnection

username = ''
gitAPI = ''
git_repo_url = ''
jenkins_key = ''
jenkins_url = ''
sql_server = ''
sql_database = ''
sql_username = ''
sql_password = ''
used_file_extensions = ''
real_result = None


def init():
    global model
    global username
    global git_repo_url
    global gitAPI
    global jenkins_key
    global jenkins_url
    global sql_server
    global sql_database
    global sql_username
    global sql_password
    global used_file_extensions

    # TODO: Change model name
    model_name = 'TestAutoModel'
    # TODO: Update list of file extensions used in your project
    used_file_extensions = ['swift', 'pdf']

    model_path = Model.get_model_path(model_name=model_name)
    model = joblib.load(model_path)

    load_dotenv(verbose=True, dotenv_path=Path('.') / 'server_files' / 'env')
    username = os.getenv("USERNAME")
    git_repo_url = os.getenv("GIT_REPO_URL")
    gitAPI = os.getenv("GIT_KEY")
    jenkins_key = os.getenv("JENKINS_KEY")
    jenkins_url = os.getenv("JENKINS_URL")
    sql_server = os.getenv("SQL_SERVER")
    sql_database = os.getenv("SQL_DATABASE")
    sql_username = os.getenv("SQL_USERNAME")
    sql_password = os.getenv("SQL_PASSWORD")


def check_if_commits_not_zero(build_data):
    if build_data['changeSet']['items'] != 0:
        return True
    else:
        return False


def drop_extra_values(row):
    del row[1]
    del row[5]


def preprocess(data):
    global real_result
    project = Project(jenkins_name=data['jenkins'], github_name=data['project'], jenkins_url=jenkins_url)
    build_data_json = project.get_build(data['build'], username, jenkins_key)

    row_list = []
    file_extensions = used_file_extensions

    file_name = data['build'] + 'INFO.json'
    if check_if_commits_not_zero(build_data_json):
        build_data = BuildData(project.jenkins_name, project.github_name, jenkins_url, file_name, build_data_json,
                               file_extensions, git_repo_url, username, gitAPI)

        real_result = build_data.real_result

        row_list = build_data.create_row_list()

        final_row_list = []
        for row in row_list:
            final_row_list.append(drop_extra_values(row))
    else:
        print("NO COMMITS, SKIPPING")
    return row_list


# TODO: Update input sample with the one generated for your model
input_sample = pd.DataFrame({'component': pd.Series(['Component.xcodeproj'], dtype='object'),
                             'change_frequency': pd.Series(['2520'], dtype='int64'),
                             'max_owners': pd.Series(['5'], dtype='int64'),
                             'dev_commits': pd.Series(['6330'], dtype='int64'),
                             'file_count': pd.Series(['5'], dtype='int64'), 'swift': pd.Series(['1'], dtype='int64'),
                             'pdf': pd.Series(['1'], dtype='int64')})
output_sample = np.array(['SUCCESS'])


@input_schema('data', PandasParameterType(input_sample))
@output_schema(NumpyParameterType(output_sample))
def predict(data):
    prediction = model.predict(data)
    return prediction


@input_schema('data', PandasParameterType(input_sample))
@output_schema(NumpyParameterType(output_sample))
def predict_proba(data):
    prediction = model.predict_proba(data)
    return prediction


def determine_if_any_failed(result):
    if "FAILURE" in result:
        print("RETURNING FAILRE")
        return "FAILURE"
    else:
        print("RETURNING SUCCESS")
        return "SUCCESS"


def generate_predictions(commits):
    result = []
    for row in commits:
        data_json_predict = ({"data": [row]})
        prediction = predict(data_json_predict['data'])
        print('RETURNED PREDICTION:', prediction)
        result.append(prediction[0])
    return result


def generate_probabilities(commits):
    probabilities_result = []
    for row in commits:
        data_json_predict = ({"data": [row]})
        prediction = predict_proba(data_json_predict['data'])
        print('RETURNED PREDICTION:', prediction)
        probabilities_result.append([prediction[0][0], prediction[0][1]])
    return probabilities_result


def generate_final_result(prediction_info, result):
    final_result = [prediction_info["project"], determine_if_any_failed(result), real_result]
    return final_result


def run(data):
    try:
        print("INPUT", data)
        prediction_info = json.loads(data)
        commits = preprocess(prediction_info)

        print("COMMITS:", commits)
        result = generate_predictions(commits)
        probabilities = generate_probabilities(commits)

        print("RESULT LIST", result)

        final_result = generate_final_result(prediction_info, result)
        print("FINAL RESULT: ", final_result)
        # Only insert prediction if there are commits
        if result:
            sql_conn = SQLConnection(sql_server, sql_database,
                                     sql_username, sql_password)
            with sql_conn:
                sql_conn.insert_prediction(final_result)
        else:
            final_result[1] = 'NO COMMITS TO PREDICT'

        print("PROBABILITIES:", probabilities)

        json_return = {"project": final_result[0],
                    "prediction": final_result[1],
                    "real result": final_result[2],
                    "result list": result,
                    "probabilities list:": probabilities}
        # You can return any data type, as long as it is JSON serializable.
        print("RETURNING JSON:", json_return)
        return json_return
    except Exception as e:
        result = str(e)
        return json.dumps({"error": result})
