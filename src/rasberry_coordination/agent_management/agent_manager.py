#! /usr/bin/env python
# ----------------------------------
# @author: jheselden
# @email: jheselden@lincoln.ac.uk
# @date:
# ----------------------------------

import copy
from copy import deepcopy
from pprint import pprint
import yaml

from rospy import Subscriber, Publisher, Service, Time

from std_msgs.msg import String as Str
from std_srvs.srv import Trigger, TriggerResponse

from rasberry_coordination.msg import MarkerDetails, KeyValuePair
from rasberry_coordination.srv import AddAgent, AgentNodePair
from rasberry_coordination.coordinator_tools import logmsg
from rasberry_coordination.encapsuators import TaskObj as Task, LocationObj as Location, ModuleObj as Module
from rasberry_coordination.task_management.__init__ import TaskDef, StageDef, InterfaceDef

from topological_navigation.route_search2 import TopologicalRouteSearch2 as TopologicalRouteSearch


class AgentManager(object):

    """ Initialisation """
    def __init__(self, callback_dict):
        self.agent_details = {}
        self.cb = callback_dict
        self.cb['format_agent_marker'] = self.format_agent_marker
        self.pause_all = False

        # Setup Services for Dynamic Fleet Management
        Service('/rasberry_coordination/dfm/add_agent',    AddAgent, self.add_agent_ros_srv)

        self.set_marker_pub = Publisher('/rasberry_coordination/set_marker', MarkerDetails, queue_size=5)

    def add_agents(self, agent_list):
        for agent in agent_list: self.add_agent(agent)
    def add_agent(self, agent_dict):
        self.agent_details[agent_dict['agent_id']] = AgentDetails(agent_dict, self.cb)
        self.format_agent_marker(self.agent_details[agent_dict['agent_id']], style='red')
        logmsg(category="null")

    """ Dynamic Fleet Management """
    def add_agent_ros_srv(self, agent_obj):
        agent_dict = self.agent_dict(agent_obj)
        if self.validate_dict(agent_dict):
            self.add_agent(self.format_dict(agent_dict))
            self.format_agent_marker(agent_dict['agent_id'], "")
            return {'success': 1, 'msg': 'agent added'}
        else:
            return {'success': 0, 'msg': 'agent unable to be added'}
    def validate_dict(self, agent_dict): return True #TODO: setup validation system
    def format_dict(self, agent_dict):
        if  agent_dict['initial_location'] == '':
            agent_dict['initial_location'] = None
        return agent_dict
    def agent_dict(self, agent_obj):
        agent_dict = dict().copy()
        agent_dict['agent_id'] = agent_obj.agent_id
        agent_dict['setup'] = dict().copy()
        agent_dict['setup']['tasks'] = [{'module': task.module, 'role': task.role} for task in agent_obj.tasks]
        agent_dict['setup']['properties'] = {prop.key:prop.value for prop in agent_obj.properties}
        agent_dict['setup']['has_presence'] = agent_obj.has_presence
        agent_dict['initial_location'] = agent_obj.initial_location
        return agent_dict

    """ Conveniences """
    def __getitem__(self, key):
        return self.agent_details[key] if key in self.agent_details else None

    """ Visuals """
    def format_agent_marker(self, agent, style):
        """ Add/modify marker to display in rviz """
        """
           Add Marker: call self.format_agent_marker(agent_id, "")
        Modify Marker: call self.format_agent_marker(agent_id, "red")
        Remove Marker: call self.format_agent_marker(agent_id, "remove")
        """
        marker = MarkerDetails()
        marker.agent_id = agent.agent_id
        marker.type = agent.properties['rviz_type']

        #Define marker color ["remove", "red", "green", "blue", "black", "white", ""]
        marker.optional_color = style

        logmsg(category="rviz", msg="Setting %s %s(%s)"%(marker.type,marker.agent_id,marker.optional_color))

        self.set_marker_pub.publish(marker)


class AgentDetails(object):
    """ Fields:
    """

    """ Initialisations """
    def __init__(self, agent_dict, callbacks):
        self.agent_id = agent_dict['agent_id']
        self.cb = callbacks
        setup = deepcopy(agent_dict['setup'])

        #Subscriptions
        self.subs = {}

        #Navigation Defaults
        self.navigation = dict()

        #Task Defaults
        self.total_tasks = 0
        self.task = Task(default=True)
        self.task_buffer = []

        self.interruption = None
        self.registration = False
        self.properties = setup['properties']

        # Define interface for each role
        # self.tasks, self.modules = Module.init_modules(self, setup['tasks'])
        self.tasks = setup['tasks']

        logmsg(category="MODULE", id=self.agent_id, msg="Initialising Module Interfaces:")
        self.modules = {t['module']: Module(agent=self, name=t['module'], role=t['role']) for t in self.tasks}

        #Location and Callbacks
        self.location = Location(presence=setup['has_presence'], initial_location=agent_dict['initial_location'])


    """ Task Starters """
    def add_idle_tasks(self):
        [self.add_task(task_name=m.idle_task_name) for m in self.modules.values() if m.name != "base"]
        if 'base' in self.modules: self.add_task(task_name=self.modules['base'].idle_task_name)

        if not self.task_buffer:
            logmsg(level="error", category="task", id=self.agent_id, msg="WARNING! Agent has no idle tasks.")
            logmsg(level="error", category="task", msg="    | All agents must be assigned a module.")
            logmsg(level="error", category="task", msg="    | Should each module have an idle task for each agent?")
            logmsg(level="error", category="task", msg="    \ Agent to be assigned a basic idle task.")
            self.add_task(task_name='idle')


    def add_task(self, task_name, task_id=None, task_stage_list=[], details={}, contacts={}, index=None, quiet=False, initiator_id=""):
        """ Called by task stages, used to buffer new tasks for the agent """
        # #picker.interface.called(): self.agent.add_task('transportation_request_courier')
        # 1. #find TaskDef
        # 2. #task = TaskDef()
        # 3. #buffer += [task] OR buffer.insert(0, [task])

        # logmsg(category="TASK", id=self.agent_id, msg="Attempting to add task: %s" % task_name)
        # logmsg(category="TASK", msg="    | Adding task: %s" % task_name)

        if task_name not in dir(TaskDef):
            logmsg(category="TASK", msg="    | %s (not found)"%task_name)
            return

        task_def = getattr(TaskDef, task_name)
        task = task_def(self, task_id=task_id, details=details, contacts=contacts, initiator_id=initiator_id)

        if not task:
            logmsg(category="TASK", msg="    | %s (empty)"%task_name)
            return

        task_name = task_name if task.name == task_name else "%s/%s"%(task_name,task.name)

        if not index: self.task_buffer += [task]
        else: self.task_buffer.insert(index, [task])

        if quiet:
            logmsg(category="DTM", msg="    |    | buffering %s to task_buffer[%i]" % (task_name, index or len(self.task_buffer)))
        else:
            logmsg(category="TASK",  msg="    | Buffering %s to task_buffer[%i]:" % (task_name, index or len(self.task_buffer)))
            [logmsg(category="TASK", msg="    |    | %s"%t) for t in task.stage_list]

    def start_next_task(self, idx=0):
        logmsg(category="TASK", id=self.agent_id, msg="Beginning next task", speech=False)

        if len(self.task_buffer) < 1: self.add_idle_tasks()
        if len(self.task_buffer) <= idx: return
        self.task = self.task_buffer.pop(idx)

        logmsg(category="TASK",  msg="- Active task: %s" % self['name'], speech=False)
        logmsg(category="TASK",  msg="  Task details:")
        [logmsg(category="TASK", msg="      | %s" % stage) for stage in self['stage_list']]


    """ Roles """
    def roles(self):
        return [m.role for m in self.modules.values()]

    """ Navigation """
    def map_cb(self, msg):
        """topological map callback
        """
        self.navigation['tmap'] = yaml.safe_load(msg.data)
        self.navigation['tmap_node_list'] = [node["node"]["name"] for node in self.navigation['tmap']['nodes']]
        self.navigation['tmap_available'] = deepcopy(self.navigation['tmap'])
        self.navigation['available_route_search'] = TopologicalRouteSearch(self.navigation['tmap_available'])
    def is_node_restricted(self, node_id):
        """checks if a given node is in the robot's restricted tmap2
        :param node_id: name of the node, str
        """
        if 'navigation_restrictions' in self.properties:
            return ('tmap_node_list' in self.navigation and node_id in self.navigation['tmap_node_list'])
        return True
    def goal(self): return self().target


    """ Conveniences for Active Task """
    def __call__(A, index=0): return A.task.stage_list[index] if len(A.task.stage_list) > index else None
    def __getitem__(A, key):  return A.task[key] if A.task else None
    def __setitem__(A, key, val):    A.task[key] = val


    """ Standard Task Interactions """
    def start_stage(self):
        self()._start()
        self()._notify_start()
        self().new_stage = False
    def end_stage(self):
        from time import sleep; sleep(0.2) #TODO: this can be removed once add task to buffer is removed from async
        logmsg(category="stage", id=self.agent_id, msg="Stage %s is over" % self['stage_list'][0])
        self()._notify_end()
        self()._end()
        self['stage_list'].pop(0)
        return None if self['stage_list'] else self['id']


    """ Task Interruption """
    def set_interrupt(self, type, module, task_id, scope, quiet=False):
        self.interruption = (type, module, task_id, scope)
        if quiet:
            logmsg(category="DTM", msg="    - interrupt attached to %s of type: (%s,%s,%s)." % (self.agent_id, type, module, task_id))
        else:
            logmsg(category="DTM", msg="Interrupt attached to %s of type: (%s,%s,%s)." % (self.agent_id, type, module, task_id))


    """ Logging """
    def __repr__(self):
        return "%s(%s)" % (self.get_class(), self.agent_id)
    def get_class(self):
        return str(self.__class__).replace("<class 'rasberry_coordination.agent_management.agent_manager.", "").replace("'>", "")

    """ GC """
    def delete_known_references(self, coordinator):
        import gc

        for m in self.modules.values():
            m.agent = None
            m.interface.agent = None

        coordinator.agent_manager.agent_details.pop(self.agent_id)  # Remove from agent manager
        coordinator.route_finder.planner.agent_details.pop(self.agent_id)  # Remove from route planner
        self.subs['tmap'].unregister()
        coordinator.AllAgentsList.pop(self.agent_id)  # Remove from coordinator

        gc.collect()

        import weakref ; a = weakref.ref(self) ; del self
        logmsg(category="DRM", msg="References remaining: (%s/1)" % len(gc.get_referrers(a())))
        if len(gc.get_referrers(a())) > 1:
            logmsg(level="error", category="DRM", msg="Remove unhandled refs in place or in AgentDetails.delete_known_references()")
        [logmsg(category="DRM", msg="    - (%s) %s" % (i+1, r)) for i, r in enumerate(gc.get_referrers(a()))]

    def __del__(self):
        logmsg(level="warn", category="DRM", id=self.agent_id, msg="Agent handler is deleted.")
        logmsg(level="warn", category="DRM", msg="Here, we must identify and unregister every subscriber")








