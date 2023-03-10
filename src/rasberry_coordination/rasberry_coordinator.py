#! /usr/bin/env python
# -----------------------------------
# @author: jheselden
# @email: jheselden@lincoln.ac.uk
# @date: 16/aug/2022
# -----------------------------------


# Standard Modules
import copy, os, time, datetime
import sys
import weakref
import yaml
from time import time as Now, sleep
from pprint import pprint
import rospy, rospkg
from rospy import Subscriber, Publisher
from std_msgs.msg import String as Str, Empty

from rasberry_coordination.interaction_management.manager import InteractionManager
from rasberry_coordination.task_management.manager import TaskManager
from rasberry_coordination.agent_management.manager import AgentManager
from rasberry_coordination.routing_management.manager import RoutingManager

from rasberry_coordination.coordinator_tools import logmsg, logmsgbreak, Rasberry_Logger
from rasberry_coordination.agent_management.location_handler import LocationObj as Location
from rasberry_coordination.task_management.containers.Module import ModuleObj as Module
from rasberry_coordination.task_management.containers.Task import TaskObj as Task
from rasberry_coordination.msg import MarkerDetails


class RasberryCoordinator(object):
    """RasberryCoordinator class definition"""
    def __init__(self, default_agents, planning_format, special_nodes):

        # Construct Sub-System Managers
        self.agent_manager = AgentManager(default_agents)
        self.routing_manager = RoutingManager(self.agent_manager, planning_format)
        self.interaction_manager = InteractionManager(self.agent_manager, self.routing_manager, special_nodes)
        self.task_manager = TaskManager(self)
        #TODO: find alternatives to passing managers into managers

        # Inisialise cross-references
        self.agent_manager.cb['force_replan'] = self.routing_manager.force_replan
        self.agent_manager.cb['trigger_replan'] = self.routing_manager.trigger_replan

    def on_shutdown(self, ):
        """on shutdown cancel all goals
        """
        logmsg(level='warn', msg='Coordinator shutting down, performing shutdown actions')

        logmsg(level='warn', msg='AgentManager shutting down, saving agent_list')
        dict_list = [a.agent_dict for a in self.agent_manager.agent_details.values()]
        with open('coordinator-loaded-agents-save-state.yaml', 'w') as file: yaml.dump(dict_list, file)
    def run(self):

        # Remappings to for commonly used functions
        get_agents      = self.get_agents
        offer_service   = self.interaction_manager.offer_service
        find_routes     = self.routing_manager.find_routes
        publish_routes  = self.routing_manager.publish_routes
        trigger_routing = self.routing_manager.trigger_routing
        interrupt_task  = self.task_manager.interrupt_task

        # Remappings for commonly referenced objects
        AM  = self.agent_manager

        # Systems for unintrusive standardised logging
        RL  = Rasberry_Logger(enable_task_logging=True)
        def l(idx): return; RL.log_minimal(idx, self.AllAgentsList)
        def logbreak(section, condition):
            if any(condition):
                logmsg(category="null")
                content = ('\033[01;04;92m', section, '\033[38;5;231m\033[0m')
                logmsg(level="info", category="SECT", id="SECTION", msg="%s%s%s"%content)

        # Timeout function for logging DTM updates
        DTM = self.task_manager.toc_interface
        Ut = Now(); #time since last DTM update
        def Update_DTM(A, DTM, Ut):
            if any([a().new_stage for a in A]) or (Now() - Ut > 5):
                DTM.UpdateTaskList();
                return Now();
            return Ut

        # Begin task progression
        l(-1)
        while not rospy.is_shutdown():

            # Add New Agents
            new_agent_buffer = AM.new_agent_buffer
            logbreak("NEW AGENTS", new_agent_buffer)
            if new_agent_buffer: AM.add_agent_from_buffer();                                      """ Add New Agents """

            # Update local list of Agents (new might have been added)
            A = get_agents()

            # Interrupt Stage Execution
            interrupts = [a.interruption for a in A]; a=None; del A
            logbreak("INTERRUPTS", interrupts)
            if any(interrupts): interrupt_task(AM.get_agent_list_copy());              """ Interrupt Stage Execution """

            # Update local list of Agents (existing might have been removed)
            A = get_agents()

            # Start Buffered Task
            logbreak("START TASK", [not a['stage_list'] for a in A])
            [a.start_next_task() for a in A if not a['stage_list']]; l(0);                   """ Start Buffered Task """

            # Start Stage
            logbreak("START STAGE", [a().new_stage for a in A])
            [a.start_stage() for a in A if a().new_stage];                                           """ Start Stage """

            # Monitoring
            Ut = Update_DTM(A, DTM, Ut);
            AM.fleet_monitoring()

            # Offer Action Services
            servicees = [a for a in A if a().interaction_required]
            if servicees: offer_service(servicees[0]); l(2);                                       """ Offer Service """

            # Find Routes
            trigger = trigger_routing(A)
            logbreak("ROUTE FIND", [trigger])
            if trigger: find_routes();                                                               """ Find Routes """

            # Publish Routes
            logbreak("ROUTE PUBLISH", [a().route_found for a in A])
            [publish_routes(a, trigger) for a in A if a().route_found]; l(3);                     """ Publish Routes """

            #Perform Stage-Completion Query
            [a()._query() for a in A]; l(4);                                                               """ Query """

            # End Stage
            logbreak("END", [a().stage_complete for a in A])
            E=[a.end_stage() for a in A if a().stage_complete];                                        """ End Stage """

            # Update DTM
            if any(E): DTM.EndTask(E);                                                   """ Update DTM w/ Completed """

            # Publish Log and Wait
            l(-2); rospy.sleep(0.2)


    def get_agents(self):
        self.AllAgentsList = self.agent_manager.get_agent_list_copy()
        return self.AllAgentsList.values()
