global TaskDef, StageDef, InterfaceDef, PropertiesDef


def set_properties(task_dict):
    from rasberry_coordination.coordinator_tools import logmsg
    global PropertiesDef
    PropertiesDef = {M['module']:M['properties'] for M in task_dict}

    logmsg(category="START",  msg="Properties: ")
    for module in task_dict:
        logmsg(category="START",  msg="    - %s"%module['module'])
        [logmsg(category="START", msg="        | %s -> %s" % (key,val)) for key,val in module['properties'].items()]


def def_tasks(clean_task_list):
    from rasberry_coordination.coordinator_tools import logmsg
    logmsg(category="null")

    task_list = ['rasberry_coordination.task_management.custom_tasks.%s' % task for task in clean_task_list]
    if 'rasberry_coordination.task_management.base' not in task_list:
        task_list.insert(0, 'rasberry_coordination.task_management.base')

    logmsg(category="START",  msg="Collecting Interface, Task, and Stage Definitions for modules: ")
    [logmsg(category="START", msg="    | %s" % module) for module in clean_task_list]

    # For each task, import the TaskDef, StageDef, and InterfaceDef to the respective dictionaries
    task_definitions = dict()
    stage_definitions = dict()
    interface_definitions = dict()
    for task in task_list:
        task_definitions[task] = __import__('%s' % task, globals(), locals(), ['TaskDef'], -1).TaskDef
        stage_definitions[task] = __import__('%s' % task, globals(), locals(), ['StageDef'], -1).StageDef
        interface_definitions[task] = __import__('%s' % task, globals(), locals(), ['InterfaceDef'], -1).InterfaceDef

    # Make these accessible through import
    global TaskDef, StageDef, InterfaceDef
    TaskDef = type('TaskDef', tuple(task_definitions.values()), dict())
    StageDef = type('StageDef', tuple(stage_definitions.values()), dict())
    InterfaceDef = type('InterfaceDef', tuple(interface_definitions.values()), dict())

    logmsg(category="START",  msg="Interfaces: ")
    [logmsg(category="START", msg="    | %s" % interface) for interface in dir(InterfaceDef) if not interface.startswith('__')]
    logmsg(category="START",  msg="Tasks: ")
    [logmsg(category="START", msg="    | %s" % task) for task in dir(TaskDef) if not task.startswith('__')]
    logmsg(category="START",  msg="Stages: ")
    [logmsg(category="START", msg="    | %s" % stage) for stage in dir(StageDef) if not stage.startswith('__')]