

from rasberry_coordination.task_management.Stages import StageDef

class TaskDef(object):
    """ Definitions for Task Initialisation Criteria """
    # Consistent attributes accessible directly, task-specific
    # attributes accessed through details dict defined on task
    # stage start.
    # Task definitions are defined in the perspective of the
    # agent handling the task.


    """ Runtime Method for Custom Task Definitions """
    @classmethod
    def load_details(cls, details):
        if 'coordinator_action_required' not in details:
            details['coordinator_action_required'] = False
        if 'replan_required' not in details:
            details['replan_required'] = False
        if 'stage_complete_flag' not in details:
            details['stage_complete_flag'] = False
        if 'new_stage' not in details:
            details['new_stage'] = True
        return details


    """ Runtime Method for Custom Task Definitions """
    @classmethod
    def generate_task(cls, agent, list, details={}):
        agent.task_details = cls.load_details(details)
        agent.task_stage_list = []

        #Create dictionary for access to each stage defined in StageDef
        stage_dict = {stage:StageDef().__getattribute__(stage)
                      for stage in dir(StageDef)
                      if not stage.startswith('__')}

        #For each required stage, append the StageDef.Stage to a list
        for S in task_stage_list:
            if S == "start_task":
                agent.task_stage_list += [stage_dict[S]()]
            else:
                agent.task_stage_list += [stage_dict[S](agent)]


    """ Initial Task Stages for Agents """
    @classmethod
    def idle_picker(cls, agent, details={}, task_id=None):
        print("idle_picker begun")
        agent.task_name = "idle_picker"
        agent.task_details = cls.load_details(details)
        agent.task_stage_list += [
            StageDef.IdlePicker(agent)
        ]
    @classmethod
    def idle_courier(cls, agent, details={}, task_id=None):
        agent.task_name = "idle_courier"
        agent.task_details = cls.load_details(details)
        agent.task_stage_list += [
            StageDef.IdleCourier(agent)
        ]
    @classmethod
    def idle_storage(cls, agent, details={}, task_id=None):
        agent.task_name = "idle_storage"
        agent.task_details = cls.load_details(details)
        agent.task_stage_list += [
            StageDef.IdleStorage(agent)
        ]




    """ Picker Logistics Transportation """
    @classmethod
    def transportation_request(cls, agent, details={}, task_id=None):
        agent.task_name = "transportation_request"
        agent.task_details = cls.load_details(details)
        agent.task_stage_list += [
            StageDef.StartTask(agent, task_id),
            StageDef.AssignCourier(agent),
            # robot has accepted task (ACCEPT)
            StageDef.AwaitCourier(agent),
            # robot has arrived (ARRIVED)
            StageDef.LoadCourier(agent),
            # task is marked as complete (INIT)
            StageDef.IdlePicker(agent) #not needed, added automatically when empty
        ]
    @classmethod
    def transportation_courier(cls, agent, details={}, task_id=None):
        agent.task_name = "transportation_courier"
        agent.task_details = cls.load_details(details)
        agent.task_stage_list += [
            StageDef.StartTask(agent, task_id),
            StageDef.NavigateToPicker(agent),
            StageDef.Loading(agent),
            StageDef.AssignStorage(agent),
            StageDef.AssignWaitNode(agent),
            StageDef.AwaitStoreAccess(agent),
            StageDef.NavigateToStorage(agent),
            StageDef.Unloading(agent),
            StageDef.IdleCourier(agent)
        ]
    @classmethod
    def transportation_storage(cls, agent, details={}, task_id=None):
        agent.task_name = "transportation_storage"
        agent.task_details = cls.load_details(details)
        agent.task_stage_list += [
            StageDef.StartTask(agent, task_id),
            StageDef.AwaitCourier(agent),
            StageDef.UnloadCourier(agent),
            StageDef.AwaitCourierExit(agent),
            StageDef.IdleStorage(agent)
        ]

    """ Trailer Logistics Transportation """
    @classmethod
    def trailer_courier(cls, agent, details={}, task_id=None):
        agent.task_details = cls.load_details(details)
        agent.task_stage_list += [
            StageDef.AssignStorage(agent),
            StageDef.AwaitStoreAccess(agent),
            StageDef.NavigateToStorage(agent),
            StageDef.Loading(agent),
            StageDef.AssignStorage(agent),
            StageDef.AssignWaitNode(agent),
            StageDef.AwaitStoreAccess(agent),
            StageDef.NavigateToStorage(agent),
            StageDef.Loading(agent),
            StageDef.IdleCourier(agent)
        ]

    """ UV Treatment """
    @classmethod
    def uv_edge_treatment(cls, agent, details={}, task_id=None):
        agent.task_stage_list += [
            ("navigation",    StageDef.Navigation(agent, details['edge_start_node'])),
            ("uv_treat_edge", StageDef.EdgeUVTreatment(agent, details['edge_end_node']))
        ]
    @classmethod
    def uv_row_treatment(cls, agent, details={}, task_id=None):
        agent.task_stage_list += [
            ("navigation",    StageDef.Navigation(agent, details['row_start_node'])),
            ("uv_treat_row",  StageDef.RowUVTreatment(agent, details['row_end_node']))
        ]

    """ Monitoring """
    @classmethod
    def data_collection_edge(cls, agent, details={}, task_id=None):
        agent.task_stage_list += [
            ("navigation",    StageDef.Navigation(agent, details['row_start_node'])),
            ("data_collection",  StageDef.EdgeDataCollection(agent, details['row_end_node']))
        ]
    @classmethod
    def data_collection_row(cls, agent, details={}, task_id=None):
        agent.task_stage_list += [
            ("navigation", StageDef.Navigation(agent, details['row_start_node'])),
            ("data_collection", StageDef.RowDataCollection(agent, details['row_end_node']))
        ]

    """ Maintenance """
    @classmethod
    def charge_robot(cls, agent, details={}, task_id=None):
        agent.task_stage_list += [
            StageDef.FindChargingNode(agent),
            StageDef.Navigation(agent),
            StageDef.WaitCharging(agent)
        ]
