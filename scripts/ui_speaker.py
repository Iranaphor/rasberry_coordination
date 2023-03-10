# -*- coding: utf-8 -*-
#! /usr/bin/env python
# ----------------------------------
# @author: jheselden
# @email: jheselden@lincoln.ac.uk
# @date:
# ----------------------------------

import sys, random, time

import rospy
from rospy import Subscriber as Sub
from std_msgs.msg import String

from rasberry_coordination.coordinator_tools import logmsg


class Speaker:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.agent_cb = Sub('/ui/speaker', String, self.callback)

    def callback(self, msg):
        logmsg(category="LOG", id=self.agent_id, msg=msg.data, speech=True)


if __name__ == '__main__':
    agent__id = sys.argv[1]
    rospy.init_node('speaker_'+agent__id, anonymous=False)

    SP = Speaker(agent__id)
    #SP.callback(String('init_complete'))

    #lines = open('/home/thorvald/.jokes').readlines()
    #finale = random.choice(lines)
    #print(finale)
    #rospy.spin()
    #SP.callback(String(finale))
    #time.sleep(7.5)
    
    rospy.spin()
