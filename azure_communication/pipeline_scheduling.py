from azureml.pipeline.core import Schedule, ScheduleRecurrence


# TODO: Set desired schedule
#   Schedule can be changed according to preferences, see:
#   https://docs.microsoft.com/en-us/azure/machine-learning/how-to-schedule-pipelines
def create_schedules(workspace, published_pipeline_id, schedule_name, experiment_name, time):
    recurrence = ScheduleRecurrence(frequency="Week", interval=1, week_days=["Monday", "Tuesday", "Wednesday",
                                                                             "Thursday", "Friday"],
                                    time_of_day=time)
    schedule = Schedule.create(workspace, name=schedule_name, pipeline_id=published_pipeline_id,
                               experiment_name=experiment_name, recurrence=recurrence,
                               wait_for_provisioning=True)


def remove_schedules(workspace, published_pipeline_id):
    schedules = Schedule.list(workspace, pipeline_id=published_pipeline_id)
    print("Found these schedules for the pipeline id {}:".format(published_pipeline_id))
    for schedule in schedules:
        print(schedule.id)
        if schedule.recurrence is not None:
            schedule_id = schedule.id
            fetched_schedule = Schedule.get(workspace, schedule_id)
            fetched_schedule.disable(wait_for_provisioning=True)
            print("Disabled schedule {}. New status is: {}".format(fetched_schedule.id, fetched_schedule.status))
