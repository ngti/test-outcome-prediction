import re
import requests
import os
from requests.auth import HTTPBasicAuth
from operator import attrgetter


class Project:
    def __init__(self, jenkins_name, github_name, jenkins_url):
        self.jenkins_name = jenkins_name
        self.github_name = github_name
        self.jenkins_url = jenkins_url

    def get_highest_build_number(self, username, jenkins_api_key):
        r = requests.post(self.jenkins_url + 'jenkins/job/' + self.jenkins_name + '/api/json',
                          auth=HTTPBasicAuth(username, jenkins_api_key))
        try:
            returned_json = r.json()
        except Exception:
            print(r)
            raise ConnectionRefusedError()

        return returned_json['builds'][0]['number']

    def get_build(self, number, username, jenkins_api_key):
        print("GET REVISION: ", self.jenkins_name, number)

        r = requests.post(self.jenkins_url + 'jenkins/job/' + self.jenkins_name + '/' + str(number)
                          + '/api/json',
                          auth=HTTPBasicAuth(username, jenkins_api_key))

        build_data = r.json()

        return build_data

    def get_build_test_report(self, number, username, jenkins_api_key):
        r = requests.post(self.jenkins_url + 'jenkins/job/' + self.jenkins_name + '/' + str(number)
                          + '/testReport/api/json',
                          auth=HTTPBasicAuth(username, jenkins_api_key))

        try:
            test_report = r.json()
            return test_report

        except Exception:
            print("NO TEST REPORT")


class BuildData(Project):
    def __init__(self, jenkins_name, github_name, file_name, build_data, current_columns, env_variables):
        super().__init__(jenkins_name, github_name, env_variables.get('jenkins_url'))
        self.file_name = file_name
        self.current_columns = current_columns
        self.git_repos_url = env_variables.get('git_repos_url')
        self.username = env_variables.get('username')
        self.git_api_key = env_variables.get('git_api_key')
        self.commits_list = build_data['changeSet']['items']
        self.real_result = build_data['result']
        self.build_number = build_data['number']
        self.changed_files = []

    def create_row_list(self):
        print("CURRENT COLUMNS:", self.current_columns)
        row_list = []

        commit_count = 0
        loop_length = len(self.commits_list)

        for commit in self.commits_list:
            commit_count += 1
            print("WRITING COMMIT: " + str(commit_count) + "/" + str(loop_length))

            row = self.create_row_from_commit(commit)
            if row is not False:
                row_list.append(row)

            print("DONE WRITING... NEXT COMMIT")
        return row_list

    def create_row_from_commit(self, commit):
        amount_of_files_changed = len(commit['affectedPaths'])

        if amount_of_files_changed <= 100:
            developer_commits = self.developer_number_of_commits(commit['authorEmail'])
            changed_file_extensions = []

            for git_file_path in commit['affectedPaths']:
                response = self.request_file_information(git_file_path)
                file_info = response.json()
                changed_file = GitFile(file_info, git_file_path, response)
                self.changed_files.append(changed_file)
                changed_file_extensions.append(changed_file.file_extension)

            highest_change_frequency = self.get_maximum_git_file_attribute('change_frequency')
            highest_amount_of_owners = self.get_maximum_git_file_attribute('amount_of_owners')
            row = [self.github_name, self.real_result,
                   highest_change_frequency.change_frequency,
                   highest_amount_of_owners.amount_of_owners,
                   developer_commits,
                   amount_of_files_changed,
                   self.file_name]
            row.extend(self.boolean_values_file_extensions(changed_file_extensions))

            # Do not add file extensions which are not in SQL, add manually later using information from log.
            if self.new_file_extensions(changed_file_extensions):
                print("NEW FILE EXTENSION FOUND: ", set(changed_file_extensions).difference(set(self.current_columns)))
                return False
            else:
                print("Yes, all changed files are in SQL and there are results")
                print("ADDING ROW: ", row)
                return row
        return False

    def new_file_extensions(self, changed_file_extensions):
        print("CHANGED FILE EXTENSIONS: ", changed_file_extensions)
        result = all(elem in self.current_columns for elem in changed_file_extensions)
        print("NEW FILE EXTENSION RESULT: ", result)
        if result and changed_file_extensions:
            return False
        else:
            return True

    def boolean_values_file_extensions(self, changed_file_extensions):
        boolean_file_values = []
        for extension in self.current_columns:
            if extension in changed_file_extensions:
                boolean_file_values.append(1)
            else:
                boolean_file_values.append(0)
        return boolean_file_values

    def get_maximum_git_file_attribute(self, attribute):
        return max(self.changed_files, key=attrgetter(attribute))

    def developer_number_of_commits(self, developer):
        response = self.request_developer_information(developer)
        developer_info = response.json()
        if 'Link' in response.headers:
            pages = re.match(r"^(.*?)(\d+)(\D*)$", response.headers["Link"])
            return len(developer_info) * int(pages.group(2))
        else:
            return len(developer_info)

    def request_developer_information(self, developer):
        response = requests.get(
            'https://api.github.com/' + self.git_repos_url + self.github_name + '/commits?author=' + developer,
            auth=HTTPBasicAuth(self.username, self.git_api_key))

        return response

    def request_file_information(self, git_file_path):
        response = requests.get('https://api.github.com/' + self.git_repos_url + self.github_name + '/commits?path='
                                + git_file_path,
                                auth=HTTPBasicAuth(self.username, self.git_api_key))
        full_response = [response]

        while 'next' in response.links.keys():
            response = requests.get(response.links['next']['url'], auth=HTTPBasicAuth(self.username, self.git_api_key))
            full_response.append(response)

        return ''.join(full_response)


class GitFile:
    def __init__(self, file_info, git_path, response):
        self.file_info = file_info
        self.git_path = git_path
        self.response = response
        self.change_frequency = self.file_change_frequency()
        self.amount_of_owners = self.count_file_owners()
        self.file_extension = self.get_file_extension()

    def file_change_frequency(self):
        return len(self.file_info)

    def count_file_owners(self):
        file_owners = []
        for commit in self.file_info:
            owner = commit['commit']['author']['email']
            if owner not in file_owners:
                file_owners.append(owner)

        return len(file_owners)

    def get_file_extension(self):
        filename, file_extension = os.path.splitext(self.git_path)
        return file_extension.replace('.', '')
