"""Transportation"""

from copy import deepcopy
from std_msgs.msg import String as Str
from rospy import Time, Duration, Subscriber, Publisher, Time
from rasberry_coordination.interaction_management.manager import InteractionDetails
from rasberry_coordination.coordinator_tools import logmsg
from rasberry_coordination.encapsuators import LocationObj as Location
from rasberry_coordination.robot import Robot as RobotInterface_Old
from rospy import Time, Duration

from rasberry_coordination.task_management.modules.base.stage_definitions import StageBase, Idle
from rasberry_coordination.task_management.modules.navigation.stage_definitions import Navigation, NavigateToAgent, NavigateToNode
from rasberry_coordination.task_management.modules.assignment.stage_definitions import InteractionResponse



try: from rasberry_coordination.task_management.__init__ import PropertiesDef as PDef, fetch_property
except: pass


class IdleStorage(Idle):
    """Used to Idle a storage agent whilst awaiting a request for admittance"""
    #TODO: change this to idle, and make this condition an interface response?
    def _query(self):
        """Complete once there exists any agents requiring storage"""
        success_conditions = [len(self.agent.modules['rasberry_transportation_pkg'].interface.details['request_admittance']) > 0] #TODO: this may prove error prone w/ _start
        self.flag(any(success_conditions))
    def _end(self):
        super(IdleStorage, self)._end()
        logmsg(category="stage", id=self.agent.agent_id, msg="admittance required: %s"%self.agent.modules['rasberry_transportation_pkg'].interface.details['request_admittance'])
class IdleFieldStorage(IdleStorage):
    def _end(self):
        """On completion, add an idle field_storage to the end of the buffer"""
        super(IdleFieldStorage, self)._end()
        self.agent.add_task(module='rasberry_transportation_pkg', name='idle')

""" Assignment-Based Task Stages (involves coordinator) """
class AssignFieldCourier(InteractionResponse):
    """Used to identify the closest field_courier."""
    def __init__(self, agent):
        """ Mark the details of the associated Interaction """
        super(AssignFieldCourier, self).__init__(agent)
        descriptor = {'module':'rasberry_transportation_pkg', 'role':'Robot'}
        self.interaction = InteractionDetails(type='search', grouping='agent_descriptor', descriptor=descriptor, style='closest_agent')
        self.contact = 'field_courier'
    def _start(self):
        super(AssignFieldCourier, self)._start()
        self.agent.format_marker(style='green')
    def _end(self):
        """ On completion, notify picker of field_courier acceptance, and assign a retrieve load task to the field_courier"""
        super(AssignFieldCourier, self)._end()

        self.agent.modules['rasberry_transportation_pkg'].interface.notify("car_ACCEPT")
        loc = self.agent.location()
        self.agent['contacts']['field_courier'].speaker("picker requested collection at %s" % (loc))
        self.agent['contacts']['field_courier'].add_task(module="rasberry_transportation_pkg",
                                                         name='retrieve_load',
                                                         task_id=self.agent['id'],
                                                         details={},
                                                         contacts={'picker': self.agent},
                                                         initiator_id=self.agent.agent_id)
class AssignFieldStorage(InteractionResponse):
    """Used to identify the closest field_storage."""
    def __init__(self, agent):
        """ Mark the details of the associated Interaction """
        super(AssignFieldStorage, self).__init__(agent)
        descriptor = {'module':'rasberry_transportation_pkg', 'role':'Storage'}
        self.interaction = InteractionDetails(type='search', grouping='agent_descriptor', descriptor=descriptor, style='closest_agent')
        self.contact = 'field_storage'
    def _end(self):
        """ On completion, notify picker of field_courier acceptance, and assign a retrieve load task to the field_courier"""
        super(AssignFieldStorage, self)._end()
        self.agent['contacts']['field_storage'].modules['rasberry_transportation_pkg'].interface.details['request_admittance'].append(self.agent.agent_id)
class AcceptFieldCourier(InteractionResponse):
    """Used to identify the closest field_storage."""
    def __init__(self, agent):
        """ Mark the details of the associated Interaction """
        super(AcceptFieldCourier, self).__init__(agent)
        self.interaction = InteractionDetails(type='search', grouping='agent_list', list=self.agent.modules['rasberry_transportation_pkg'].interface.details['request_admittance'], style='closest_agent')
        self.contact = 'field_courier'
    def _end(self):
        """ On completion, notify picker of field_courier acceptance, and assign a retrieve load task to the field_courier"""
        super(AcceptFieldCourier, self)._end()
        logmsg(category="stage", msg="Admitted: %s from %s" % (self.agent['contacts']['field_courier'].agent_id, self.agent.modules['rasberry_transportation_pkg'].interface.details['request_admittance']))
        logmsg(category="stage", msg="AcceptFieldCourier: stage_complete=%s" % self.stage_complete)
        self.agent.modules['rasberry_transportation_pkg'].interface.details['request_admittance'].remove(self.agent['contacts']['field_courier'].agent_id)
class AssignHeadNodeIdle(InteractionResponse):
    """Used to identify the closest available head node."""
    def __init__(self, agent):
        """ Mark the details of the associated Interaction """
        super(AssignHeadNodeIdle, self).__init__(agent)
        self.interaction = InteractionDetails(type='search', grouping='head_nodes', style='head_node_allocator')
        self.contact = 'head_node'
    """Used to identify the closest available base_node."""
    def _start(self):
        super(AssignHeadNodeIdle, self)._start()
        self.accepting_new_tasks = True
    def _query(self):
        """Complete once action has generated a result"""
        success_conditions = [self.interaction.response != None,
                              len(self.agent.task_buffer) > 0]
        self.flag(any(success_conditions))




""" Idle for Pending """
class AwaitFieldCourier(Idle):
    """Used to idle the agent until a field_courier has arrived"""
    def __repr__(self):
        """Attach id of agent to class name"""
        if 'field_courier' in self.agent['contacts']:
            return "%s(%s|%s)"%(self.get_class(), self.agent.location(), self.agent['contacts']['field_courier'].agent_id)
        else:
            return "%s()" % (self.get_class())
    def _start(self):
        super(AwaitFieldCourier, self)._start()
        self.agent['details']['arrived'] = False
        self.initial_target = self.agent.location(accurate=True)
    def _query(self):
        """Complete once the associated field_courier has arrived at the agents location"""
        success_conditions = [self.agent['details']['arrived']]
        self.flag(any(success_conditions))
    def _end(self):
        """On completion, notify the picker of ARRIVAL"""
        self.agent.modules['rasberry_transportation_pkg'].interface.notify("car_ARRIVED")
class AwaitStoreAccess(Idle):
    """Used to idle the field_courier until the storage location has accepted admittance"""
    def __repr__(self):
        """Attach id of agent to class name"""
        if self.storage_type in self.agent['contacts']:
            return "%s(%s)"%(self.get_class(), self.agent['contacts'][self.storage_type].agent_id)
        return "%s()" % (self.get_class())
    def __init__(self, agent, storage_type):
        super(AwaitStoreAccess, self).__init__(agent)
        self.storage_type = storage_type
    def _query(self):
        """Complete if the field_courier assigned to the storage of interest is this agent"""
        storage = self.agent['contacts'][self.storage_type]
        if 'field_courier' not in storage['contacts']: return
        field_courier = storage['contacts']['field_courier']
        success_conditions = [field_courier.agent_id == self.agent.agent_id]
        self.flag(any(success_conditions))
class AwaitFieldStorageAccess(AwaitStoreAccess):
    """Used to Idle the Field Courier till the field_storage accepts admittance"""
    def __init__(self, agent):
        """Specify the """
        super(AwaitFieldStorageAccess, self).__init__(agent, storage_type='field_storage')

""" Transportation Navigation Subclasses """
class NavigateToPicker(NavigateToAgent):
    """Used to define the target for the navigation as the picker"""
    def __init__(self, agent):
        """Set navigation target as associated picker"""
        super(NavigateToPicker, self).__init__(agent,  association='picker')
    def _query(self):
        """Complete when the agents location is identical to the target location."""
        picker_loc = self.agent['contacts']['picker'].location(accurate=False)
        robot_loc = self.agent.location(accurate=True)
        success_conditions = [robot_loc == self.target,
                              robot_loc == picker_loc,
                              self.agent.location.current_node == None and picker_loc in self.agent.location.closest_edge]
        self.flag(any(success_conditions))
    def _end(self):
        """End navigation by refreshing routes for other agents in motion."""
        logmsg(category="stage", id=self.agent.agent_id, msg="Navigation from %s to %s is completed." % (self.agent.location(accurate=True), self.target))
        self.agent['contacts']['picker']['details']['arrived'] = True
        self.agent.navigation_interface.cancel_execpolicy_goal() #<- since checking if at picker early, we need to end route manually
        self.target = None
        self.route_required = False
        self.agent.cb['trigger_replan']()  # ReplanTrigger

class NavigateToFieldStorage(NavigateToAgent):
    """Used to define the target for the navigation as the field_storage"""
    def __init__(self, agent):
        """Set navigation target as associated field_storage"""
        super(NavigateToFieldStorage, self).__init__(agent, association='field_storage')
    def _end(self):
        self.agent['contacts']['field_storage']['details']['arrived'] = True
class NavigateToHeadNodeIdle(NavigateToNode):
    """ Used to Navigate To Base node, but with interruption enabled """
    def __init__(self, agent):
        """Call super to set association to base_node"""
        super(NavigateToHeadNodeIdle, self).__init__(agent, association='head_node')
    def _start(self):
        """ enable interuption """
        super(NavigateToHeadNodeIdle, self)._start()
        self.accepting_new_tasks = True
    def _query(self):
        """Complete when the agents location is identical to the target location."""
        success_conditions = [self.agent.location(accurate=True) == self.target,
                              len(self.agent.task_buffer) > 0]
        self.flag(any(success_conditions))

""" FieldCourier Load Modifiers """
class TimeoutFlagModifier(StageBase):
    """Used to idle till timeout or a flag is set"""
    def _start(self, timeout_type, flag, default, prompt="move"):
        """Define the completion flag and timeout"""
        super(TimeoutFlagModifier, self)._start()
        self.agent[flag] = default
        self.trigger_flag = flag
        self.default = default
        self.timeout = Duration(secs=fetch_property('rasberry_transportation_pkg', timeout_type))
        self.timeout_prompt = False
        self.agent['contacts']['field_courier'].speaker("Arrived to %s... I will leave in %s seconds. Please %s trays." %
                                                         (self.agent.location(), str(self.timeout.secs), prompt))
    def _query(self):
        """Complete once has_tray flag is triggered by interface or timeout completes"""
        success_conditions = [Time.now() - self.start_time > self.timeout,
                              self.agent[self.trigger_flag] != self.default]
        self.flag(any(success_conditions))
        if (not self.timeout_prompt):
            time_spent = (Time.now() - self.start_time)
            if self.timeout - time_spent < Duration(secs=10):
               self.timeout_prompt = True
               self.agent['contacts']['field_courier'].speaker("I will leave in 10 seconds.")

    def _end(self):
        """On Completion, set the field_courier's flag and notify picker"""
        super(TimeoutFlagModifier, self)._end()
        self.agent['contacts']['field_courier'][self.trigger_flag] = self.default
        if "STD_v2_" in self.agent.agent_id:
            self.agent.modules['rasberry_transportation_pkg'].interface.notify("car_INIT")
        else:
            self.agent.modules['rasberry_transportation_pkg'].interface.notify("car_COMPLETE")
class LoadFieldCourier(TimeoutFlagModifier):
    """Used to define completion details for when the field_courier can be considered loaded"""
    def _start(self):
        """Define the flag default as True and the timeout as the transportation/wait_loading property"""
        super(LoadFieldCourier, self)._start(timeout_type='wait_loading', flag='has_tray', default=True, prompt="load")
        self.agent.format_marker(style='blue')
class UnloadFieldCourier(TimeoutFlagModifier):
    """Used to define completion details for when the field_courier can be considered unloaded"""
    def _start(self):
        """Define the flag default as False and the timeout as the transportation/wait_unloading property"""
        super(UnloadFieldCourier, self)._start(timeout_type='wait_unloading', flag='has_tray', default=False, prompt="unload")
""" Loading Modifiers for Courier """
class Loading(StageBase):
    """Used for awaiting a change-of-state from the picker"""
    def _start(self):
        super(Loading, self)._start()
    def _query(self):
        """Complete once agents's has_tray flag is true"""
        success_conditions = [self.agent['has_tray'] == True]
        self.flag(any(success_conditions))
    def _end(self):
        """On completion, increment the field_courier's total load by 1"""
        super(Loading, self)._end()
        self.agent.local_properties['load'] += 1
class Unloading(StageBase):
    """Used for awaiting a change-of-state from the storage"""
    def _query(self):
        """Complete once agents's has_tray flag is false"""
        success_conditions = [self.agent['has_tray'] == False]
        self.flag(any(success_conditions))
    def _end(self):
        """On completion, reset the field_courier's total load to 0"""
        super(Unloading, self)._end()
        self.agent.local_properties['load'] = 0
