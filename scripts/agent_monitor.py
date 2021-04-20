# -*- coding: utf-8 -*-
#! /usr/bin/env python
# ----------------------------------
# @author: jheselden
# @email: jheselden@lincoln.ac.uk
# @date:
# ----------------------------------

import sys

import rospy
from rospy import Subscriber as Sub
from rasberry_coordination.msg import KeyValuePair

class diagnostic_printout:
    def __init__(self, agent_id, type):
        """ Class to output live details about a given agent.

        :attr agent_dict: define default properties which may not be published but are needed for display.

        :param agent_id: the unique identifier for the agent
        :param type: the agents type [robot/picker]
        """
        self.circles = {}
        self.init_circles()
        self.type = type
        self.agent_dict = {"agent_id": agent_id, "task_id": None, "task_stage": None,
                           "current_node": None, "previous_node": None, "closest_node": None}
        self.agent_cb = Sub('/rasberry_coordination/agent_monitor/'+agent_id, KeyValuePair, self.callback)

    def init_circles(self):
        """ Define progress indicators and save references to self.circles

        :return: None
        """
        e0 = u"     ▄▄▀▀▀▀▀▀▄▄     "
        e1 = u"   ▄▀          ▀▄   "
        e2 = u"  ▄▀            ▀▄  "
        e3 = u" ▄▀              ▀▄ "
        e4 = u" █                █ "
        e5 = u" ▀▄              ▄▀ "
        e6 = u"  ▀▄            ▄▀  "
        e7 = u"   ▀▄          ▄▀   "
        e8 = u"     ▀▀▄▄▄▄▄▄▀▀     "
        EMPTY = [e0, e1, e2, e3, e4, e5, e6, e7, e8]

        x0 = u"     ▄▄▀▀▀███▄▄     "
        x1 = u"   ▄▀     ██████▄   "
        x2 = u"  ▄▀      ███████▄  "
        x3 = u" ▄▀       ██████▀▀▄ "
        x4 = u" █        ██▀▀    █ "
        x5 = u" ▀▄              ▄▀ "
        x6 = u"  ▀▄            ▄▀  "
        x7 = u"   ▀▄          ▄▀   "
        x8 = u"     ▀▀▄▄▄▄▄▄▀▀     "
        FIFTH = [x0, x1, x2, x3, x4, x5, x6, x7, x8]

        x0 = u"     ▄▄▀▀▀███▄▄     "
        x1 = u"   ▄▀     ██████▄   "
        x2 = u"  ▄▀      ███████▄  "
        x3 = u" ▄▀       ████████▄ "
        x4 = u" █        █████████ "
        x5 = u" ▀▄              ▄▀ "
        x6 = u"  ▀▄            ▄▀  "
        x7 = u"   ▀▄          ▄▀   "
        x8 = u"     ▀▀▄▄▄▄▄▄▀▀     "
        QUATER = [x0, x1, x2, x3, x4, x5, x6, x7, x8]

        x0 = u"     ▄▄▀▀▀███▄▄     "
        x1 = u"   ▄▀     ██████▄   "
        x2 = u"  ▄▀      ███████▄  "
        x3 = u" ▄▀       ████████▄ "
        x4 = u" █        █████████ "
        x5 = u" ▀▄        ▀██████▀ "
        x6 = u"  ▀▄         ▀███▀  "
        x7 = u"   ▀▄          █▀   "
        x8 = u"     ▀▀▄▄▄▄▄▄▀▀     "
        FIFTH2 = [x0, x1, x2, x3, x4, x5, x6, x7, x8]

        x0 = u"     ▄▄▀▀▀███▄▄     "
        x1 = u"   ▄▀     ██████▄   "
        x2 = u"  ▄▀      ███████▄  "
        x3 = u" ▄▀       ████████▄ "
        x4 = u" █        █████████ "
        x5 = u" ▀▄       ████████▀ "
        x6 = u"  ▀▄      ███████▀  "
        x7 = u"   ▀▄     ██████▀   "
        x8 = u"     ▀▀▄▄▄███▀▀     "
        HALF = [x0, x1, x2, x3, x4, x5, x6, x7, x8]

        x0 = u"     ▄▄▀▀▀███▄▄     "
        x1 = u"   ▄▀     ██████▄   "
        x2 = u"  ▄▀      ███████▄  "
        x3 = u" ▄▀       ████████▄ "
        x4 = u" █        █████████ "
        x5 = u" ▀▄     ▄█████████▀ "
        x6 = u"  ▀▄  ▄██████████▀  "
        x7 = u"   ▀▄███████████▀   "
        x8 = u"     ▀▀██████▀▀     "
        FIFTH3 = [x0, x1, x2, x3, x4, x5, x6, x7, x8]

        x0 = u"     ▄▄▀▀▀███▄▄     "
        x1 = u"   ▄▀     ██████▄   "
        x2 = u"  ▄▀      ███████▄  "
        x3 = u" ▄▀       ████████▄ "
        x4 = u" █        █████████ "
        x5 = u" ▀████████████████▀ "
        x6 = u"  ▀██████████████▀  "
        x7 = u"   ▀████████████▀   "
        x8 = u"     ▀▀██████▀▀     "
        QUATER3 = [x0, x1, x2, x3, x4, x5, x6, x7, x8]

        x0 = u"     ▄▄▀▀▀███▄▄     "
        x1 = u"   ▄▀     ██████▄   "
        x2 = u"  ▄▀      ███████▄  "
        x3 = u" ▄█▄▄     ████████▄ "
        x4 = u" ██████▄▄ █████████ "
        x5 = u" ▀████████████████▀ "
        x6 = u"  ▀██████████████▀  "
        x7 = u"   ▀████████████▀   "
        x8 = u"     ▀▀██████▀▀     "
        FIFTH4 = [x0, x1, x2, x3, x4, x5, x6, x7, x8]

        f0 = u"     ▄▄██████▄▄     "
        f1 = u"   ▄████████████▄   "
        f2 = u"  ▄██████████████▄  "
        f3 = u" ▄████████████████▄ "
        f4 = u" ██████████████████ "
        f5 = u" ▀████████████████▀ "
        f6 = u"  ▀██████████████▀  "
        f7 = u"   ▀████████████▀   "
        f8 = u"     ▀▀██████▀▀     "
        FULL = [f0, f1, f2, f3, f4, f5, f6, f7, f8]

        self.circles = {"0/1": EMPTY, "1/5": FIFTH,  "1/4": QUATER,
                                      "2/5": FIFTH2, "1/2": HALF,
                                      "3/5": FIFTH3, "3/4": QUATER3,
                                      "4/5": FIFTH4, "1/1": FULL}

    def callback(self, msg):
        """ Callback from ['/rasberry_coordination/agent_monitor/%s' % agent_id] to detail changes to the AgentDetails
        object managed by the coordinator.

        For each call, redraw the monitor display:
        > identify progression chart with self.get_task_completion_percentage
        > attach details from agent_dict in the order defined by printable_fields
        > empty fields in printable_fields will not print a ":"

        :param msg: KayValuePair {'key':agent_attribute, 'val':value}
        :return: None
        """
        print(msg)
        self.agent_dict[msg.key] = msg.value
        printable_fields = ["agent_id", "", "task_id", "task_stage", "",
                            "current_node", "previous_node", "closest_node", "registered"]
        print("\n" * 80)  # divider
        circle = self.get_task_completion_percentage()
        for i, row in enumerate(circle):
            tag = printable_fields[i]
            if tag in self.agent_dict:
                print(row + "  |  " + tag + ": " + str(self.agent_dict[tag]))
            else:
                print(row + "  |  ")

    def get_task_completion_percentage(self):
        """ Based on the type of agent, and its current task_stage, return the appropriate progress indicator.

        :return: List of utf strings representing a progress indicator for the task.
        """
        if self.type == "robot":
            task_states = {"go_to_picker": "0/1", "wait_loading": "1/4", "go_to_storage": "1/2", "wait_unloading": "3/4",
                           "go_to_base": "1/1", str(None): "1/1", "paused": "0/1"}
        elif self.type == "picker":
            task_states = {"CREATED": "0/1", "CALLED": "0/1",
                           "ASSIGNED": "2/5", "ACCEPT": "2/5",
                           "ARRIVED": "3/5",
                           "LOADED": "1/1", "ABANDONED": "1/1", "DELIVERED": "1/1", str(None): "1/1"}
        return self.circles[task_states[str(self.agent_dict["task_stage"])]]


if __name__ == '__main__':
    agent_id = sys.argv[1]
    type = sys.argv[2]
    rospy.init_node('agent_monitor_'+agent_id, anonymous=False)

    DP = diagnostic_printout(agent_id, type)
    DP.callback(KeyValuePair('agent_id', agent_id))
    rospy.spin()