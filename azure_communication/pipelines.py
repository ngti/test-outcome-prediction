import os
import pathlib
from azureml.core import Experiment
from azureml.pipeline.core import Pipeline, StepSequence, PipelineParameter, PipelineData, TrainingOutput
from azureml.pipeline.steps import PythonScriptStep, AutoMLStep
from azureml.train.automl import AutoMLConfig

# TODO: Change desired settings for automated machine learning.
#       See here for more info:
automl_settings = {
    "experiment_timeout_minutes": 20,
    "max_concurrent_iterations": 5,
    "primary_metric": 'norm_macro_recall'
}


class PipelineRegister:
    def __init__(self, aml_compute, run_amlcompute, prepped_data_path, workspace, env_variables):
        self.aml_compute = aml_compute
        self.run_amlcompute = run_amlcompute
        self.prepped_data_path = prepped_data_path
        self.ws = workspace
        self.env_variables = env_variables
        self.path = str(pathlib.Path(__file__).parent.absolute()) + '/'
        self.prepped_data = None
        self.model_data = None

    def setup_dataprep_step(self):
        source_directory = self.path + 'azure_pipeline_steps/dataprep'
        print('Source directory for the step is {}.'.format(os.path.realpath(source_directory)))

        dataprep_step = PythonScriptStep(name="dataprep",
                                         script_name="dataprep.py",
                                         compute_target=self.aml_compute,
                                         source_directory=source_directory,
                                         allow_reuse=False,
                                         params=self.env_variables,
                                         runconfig=self.run_amlcompute,
                                         arguments=["--output_path", self.prepped_data_path],
                                         outputs=[self.prepped_data_path])
        return dataprep_step

    def setup_training_step(self):
        prepped_data = self.prepped_data_path.parse_parquet_files(file_extension=None)
        project_folder = './automl'

        automl_config = AutoMLConfig(compute_target=self.aml_compute,
                                     task="classification",
                                     training_data=prepped_data,
                                     label_column_name="test_result",
                                     path=project_folder,
                                     enable_early_stopping=True,
                                     featurization='auto',
                                     debug_log="automl_errors.log",
                                     n_cross_validations=10,
                                     **automl_settings
                                     )

        ds = self.ws.get_default_datastore()
        metrics_output_name = 'metrics_output'
        best_model_output_name = 'model_output'

        metrics_data = PipelineData(name='metrics_data',
                                    datastore=ds,
                                    pipeline_output_name=metrics_output_name,
                                    training_output=TrainingOutput(type='Metrics'))
        model_data = PipelineData(name='best_model_data',
                                  datastore=ds,
                                  pipeline_output_name=best_model_output_name,
                                  training_output=TrainingOutput(type='Model'))

        self.model_data = model_data

        automl_step = AutoMLStep(
            name='automl_module',
            automl_config=automl_config,
            passthru_automl_config=False,
            outputs=[metrics_data, model_data],
            allow_reuse=True)

        return automl_step

    def setup_deploy_step(self):
        model_name = PipelineParameter("model_name", default_value="TestAutoModel")

        source_directory = self.path + 'azure_pipeline_steps/deploy'
        print('Source directory for the step is {}.'.format(os.path.realpath(source_directory)))

        deploy_step = PythonScriptStep(name="deploy",
                                       script_name="deploy.py",
                                       compute_target=self.aml_compute,
                                       source_directory=source_directory,
                                       allow_reuse=False,
                                       params=self.env_variables,
                                       runconfig=self.run_amlcompute,
                                       arguments=["--model_name", model_name, "--model_path", self.model_data],
                                       inputs=[self.model_data])

        return deploy_step

    def create_pipeline(self, steps):
        step_sequence = StepSequence(steps=steps)

        train_pipeline = Pipeline(workspace=self.ws, steps=step_sequence)
        train_pipeline.validate()
        print("Pipeline register built and validated")

        Experiment(self.ws, 'Register-train-deploy').submit(train_pipeline, regenerate_outputs=False)
        print("Register, train and deploy experiment created and submitted")


class PipelineCollection:
    def __init__(self, aml_compute, run_amlcompute, workspace, env_variables):
        self.aml_compute = aml_compute
        self.run_amlcompute = run_amlcompute
        self.ws = workspace
        self.env_variables = env_variables
        self.path = str(pathlib.Path(__file__).parent.absolute()) + '/'

    def setup_data_collection_step(self):
        source_directory = self.path + 'azure_pipeline_steps/collection'
        data_collection_step = PythonScriptStep(name="data_collection",
                                                script_name="collect_reports.py",
                                                compute_target=self.aml_compute,
                                                source_directory=source_directory,
                                                allow_reuse=False,
                                                params=self.env_variables,
                                                runconfig=self.run_amlcompute)
        return data_collection_step

    def setup_preprocessing_step(self):
        source_directory = self.path + 'azure_pipeline_steps/preprocessing'
        preprocessing_step = PythonScriptStep(name="preprocessing",
                                              script_name="preprocess.py",
                                              compute_target=self.aml_compute,
                                              source_directory=source_directory,
                                              allow_reuse=False,
                                              params=self.env_variables,
                                              runconfig=self.run_amlcompute)
        return preprocessing_step

    def create_pipeline(self, steps):
        step_sequence = StepSequence(steps=steps)

        collection_preprocessing_pipeline = Pipeline(workspace=self.ws, steps=[step_sequence])
        collection_preprocessing_pipeline.validate()
        print("Collection and preprocessing pipeline built and validated")

        return Experiment(self.ws, 'Collection-preprocessing').submit(collection_preprocessing_pipeline,
                                                                          regenerate_outputs=False)
