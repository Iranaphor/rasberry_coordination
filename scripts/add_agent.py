#!/usr/bin/env python

import tf
import sys
import rospy
import os
import json, yaml
from std_msgs.msg import String
import rasberry_coordination
from rasberry_coordination.msg import NewAgentConfig, Module
from diagnostic_msgs.msg import KeyValue
import rasberry_des.config_utils
from rasberry_coordination.coordinator_tools import logmsg, logmsgbreak
from pprint import pprint
import rospkg
from geometry_msgs.msg import Pose

def get_kvp_list(dict, item):
    if item in dict:
        return [KeyValue(k, str(v)) for k, v in dict[item].items()]
    return []


def get_file_path(setup):
    folder = os.getenv('AGENT_SETUP_CONFIG', None)
    #folder = '/home/thorvald/rasberry_ws/src/RASberry/rasberry_core/config/site_files/default_farm/default_field/server/setup/'
    setup_file = "%s%s.yaml"%(folder, setup)
    return setup_file


def load_agent_obj(agent_id, setup, printer=True):

    # Identify agent and setup filepaths
    setup_file = get_file_path(setup)

    # Load file contents, (fallback on empty file if agent_file not found)
    agent_data = {'agent_id': agent_id.split("/")[-1].split(".")[0]}
    if printer: logmsg(level="warn", category="DRM", msg="Launching with agent_data: %s" % (agent_data))


    # Build msg (use yaml.dump to parse further details through to coordinator)
    setup_data = rasberry_des.config_utils.get_config_data(setup_file)
    pprint(setup_data)
    print("\n")

    agent = NewAgentConfig()
    agent.agent_id = agent_data['agent_id']
    agent.local_properties = get_kvp_list(agent_data, 'local_properties')

    for m in setup_data['modules']:
        m['details'] = m['details'] if 'details' in m else [{'key':'value'}]

    agent.modules = [Module(m['name'], m['interface'], [KeyValue(d.keys()[0], yaml.dump(d.values()[0])) for d in m['details']]) for m in setup_data['modules']]
    print("\n\n")
    return agent


class AgentMonitor():
    def __init__(self):
        self.pub = rospy.Publisher("/rasberry_coordination/dynamic_fleet/add_agent", NewAgentConfig, latch=True, queue_size=5)
        self.s1 = rospy.Subscriber("/car/new_agent", String, self.load,  callback_args='picker')
        self.s2 = rospy.Subscriber("/sar/new_agent", String, self.load,  callback_args='tall_controller')
        self.s3 = rospy.Subscriber("/car/new_store", String, self.load,  callback_args='storage')
        self.s4 = rospy.Subscriber('/car_client/get_gps', String, self.add_car_agent)

    """ Dynamic Fleet """
    def add_car_agent(self, msg):
        details = json.loads(msg.data)
        id = str(details['user'])
        if 'STD_v2' in id:
            self.load(String(id), 'picker', printer=False)

    def load(self, msg, agent_type, printer=True):
        logmsg(category="DRM", msg="Recieved new %s information: %s"%(msg.data, agent_type))
        agent = load_agent_obj(agent_id=msg.data, setup=agent_type, printer=printer)
        if printer: print(agent)
        self.pub.publish(agent)


if __name__ == '__main__':
    # Initialise node
    rospy.init_node("AddAgent", anonymous=True)
    rospy.sleep(1)

    if len(sys.argv) < 5:
        logmsg(category="DRM", msg="AddAgent Monitor launched")
        monitor = AgentMonitor()
        rospy.spin()

    else:
        logmsg(category="DRM", msg="AddAgent Node launched")

        # Collect details
        agent_id = sys.argv[1]
        setup = sys.argv[2]

        logmsgbreak()
        logmsg(category="DRM", msg="Loading configurations:")
        logmsg(category="DRM", msg="    - agent_file: %s"%agent_id)
        logmsg(category="DRM", msg="    - setup_file: %s"%setup)

        agent = load_agent_obj(agent_id, setup)
        logmsg(category="DRM", msg="Details of Agent being launched:\n%s\n\n"%agent)

        # Create publisher
        pub = rospy.Publisher("/rasberry_coordination/dynamic_fleet/add_agent", NewAgentConfig, latch=False, queue_size=5)
        rospy.sleep(1)

        # Create a storage point for the robots pose to be saved on shutdown
        msg_store = {'pose': Pose()}
        def save(msg):
            msg_store['pose'] = msg
        sub = rospy.Subscriber("/robot_pose", Pose, save)

        while not rospy.is_shutdown():
            pub.publish(agent)
            logmsg(category="null", msg="publishing")
            rospy.sleep(5)

        #On shutdown, save the robots last known location to a file for loading at boot
        filepath = rospkg.RosPack().get_path('rasberry_core')+"/new_tmule/robots/history/%s.sh"%(agent.agent_id)
        with open(filepath, 'w') as f:
            o = msg_store['pose'].orientation
            rot = tf.transformations.euler_from_quaternion([o.x, o.y, o.w, o.z])[2]
            f.write('export_override ROBOT_POS_A %s\n'%rot)
            f.write('export_override ROBOT_POS_X %s\n'%msg_store['pose'].position.x)
            f.write('export_override ROBOT_POS_Y %s\n'%msg_store['pose'].position.y)

