import os
from azure.storage.blob import BlobProperties, ContentSettings, BlobServiceClient


class AzureBlobStorage:
    def __init__(self, container, temp_folder, azure_connection):
        self.service_client = BlobServiceClient.from_connection_string(azure_connection)
        self.container = container
        self.container_client = self.setup_container_client()
        self.temp_folder = temp_folder

    def setup_container_client(self):
        return self.service_client.get_container_client(self.container)

    def list_blobs_for_project(self, project):
        print("LIST BLOBS FOR PROJECT", project)
        blobs_list = self.container_client.list_blobs(name_starts_with=project)
        blobs = []
        for blob in blobs_list:
            blobs.append(blob.name)

        return blobs

    def upload_blob(self, file_name):
        content_settings = ContentSettings(content_type='application/json')
        file_temp_folder = self.temp_folder + file_name
        blob_client = self.service_client.get_blob_client(container=self.container,
                                                          blob=BlobProperties(name=file_name))

        with open(file_temp_folder, 'rb') as data:
            blob_client.upload_blob(data)

        # Set type to application/json, access tier to hot and delete temp files
        blob_client.set_http_headers(content_settings=content_settings)
        blob_client.set_standard_blob_tier(standard_blob_tier='Hot')

    def download_blobs_to_local_temp_folder(self, project):
        blobs_list = self.list_blobs_for_project(project)

        # Remove last blob to keep one on Azure Blob Storage
        blobs_list.pop()
        print("BLOBS FOUND: ", project, blobs_list)
        for file in blobs_list:
            print("DOWNLOADING BLOB: ", file)
            blob_client = self.service_client.get_blob_client(container=self.container,
                                                              blob=BlobProperties(name=file))

            os.makedirs(self.temp_folder + '/' + project, exist_ok=True)

            with open(self.temp_folder + '/' + file, "wb") as my_blob:
                download_stream = blob_client.download_blob()
                my_blob.write(download_stream.readall())

    def delete_blob_from_main_storage(self, jenkins_name, file_name):
        file_dir = jenkins_name + '/' + file_name
        blob_client = self.service_client.get_blob_client(container=self.container,
                                                          blob=BlobProperties(name=file_dir))
        # Delete blob from main 'Hot' folder - later upload it to Archive
        blob_client.delete_blob(delete_snapshots='include')

    def upload_blob_to_archive(self, jenkins_name, file_name):
        file_dir = jenkins_name + '/' + file_name
        content_settings = ContentSettings(content_type='application/json')
        blob_client = self.service_client.get_blob_client(container=self.container,
                                                          blob=BlobProperties(name='archive/' + file_dir))

        with open(self.temp_folder + '/' + file_dir, 'rb') as data:
            blob_client.upload_blob(data)

        # Set type to application/json, access tier to COLD and delete temp files
        blob_client.set_http_headers(content_settings=content_settings)
        blob_client.set_standard_blob_tier(standard_blob_tier='Cool')

    def delete_blobs_from_local_temp_folder(self, project):
        print("DELETING BLOBS FROM TEMP FOLDER...")
        for file in os.listdir(self.temp_folder + '/' + project + '/'):
            os.remove(self.temp_folder + '/' + project + '/' + file)
            print("DELETED ", file)
