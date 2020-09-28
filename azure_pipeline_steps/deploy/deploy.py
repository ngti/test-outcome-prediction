from azureml.core.model import Model, InferenceConfig
from azureml.core.run import Run
from azureml.core.webservice import AciWebservice
import argparse


def deploy():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", required=True)
    parser.add_argument("--model_path", required=True)
    args = parser.parse_args()

    print(f"model_name : {args.model_name}")
    print(f"model_path: {args.model_path}")

    run = Run.get_context()
    ws = run.experiment.workspace

    model = Model.register(workspace=ws,
                           model_path=args.model_path,
                           model_name=args.model_name)

    print("Registered version {0} of model {1}".format(model.version, model.name))

    inference_config = InferenceConfig(entry_script='score.py', runtime='python',
                                       conda_file='conda.yml',
                                       extra_docker_file_steps='extra_docker_steps',
                                       source_directory='server_files/')
    deployment_config = AciWebservice.deploy_configuration(cpu_cores=0.1, memory_gb=0.5, auth_enabled=True)

    try:
        service = AciWebservice(ws, "testscorescriptauto")
        service.update(models=[model])
        print("EXISTING ENDPOINT FOUND: MODEL UPDATED")
    except Exception:
        Model.deploy(ws, "testscorescriptauto", [model], inference_config, deployment_config)
        print("NO EXISTING ENDPOINT FOUND: DEPLOYED MODEL TO NEW ENDPOINT")


if __name__ == '__main__':
    deploy()
