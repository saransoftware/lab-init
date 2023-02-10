#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: dsmadmc
short_description: Executes or simulates dsmadmc with given args
version_added: "2.4"
description:
    - Same as command module but only for dmsadmc. You can use the shortened
      parameter names as options. The used parameters are
      used to compile the whole command. See RETRUN for details.
options:
    command:
        description:
            - Command to be executed on the TSM server.
        required: true
        type: string
    se[rveraddress]:
        description:
            - Specifies the server stanza in the dsm.sys file. The client uses
              the server stanza to determine the server it connects to.
        required: true
    id:
        description:
            - Specifies the administrator's user ID.
        required: true
        type: string
    pa[ssword]:
        description:
            - Specifies the administrator's password. Not logged.
        required: true
        type: string
    dataonly:
        description:
            - NO or YES
              Specifies whether product version information and output headers
              display with the output.
        required: false
        type: bool
        default: 'NO'
    comma[delimited]:
        description:
            - Specifies that any tabular output from a server query is to be
              formatted as comma-separated strings rather than in readable
              format. This option is intended to be used primarily when you
              redirect the output of an SQL query (SELECT command). The
              comma-separated value format is a standard data format, which can
              be processed by many common programs, including spreadsheets,
              databases, and report generators.
        required: false
        type: bool
        default: true
    tab[delimited]:
        description:
            - Specifies that any tabular output from a server query is to be
              formatted as tab-separated strings rather than in readable format.
              This option is intended to be used primarily when you redirect the
              output of an SQL query (SELECT command). The tab-separated value
              format is a standard data format, which can be processed by many
              common programs, including spreadsheets, databases, and report
              generators.
        required: false
        type: bool
        default: false
    displ[aymode]:
        description:
            - LISt or TABle
            You can force the QUERY output to tabular or list format
            regardless of the command-line window column width.
            If you are using the -DISPLAYMODE option and you want the output
            to go to a file, do not specify the -OUTFILE option. Use redirection
            to write to the file.
        required: false
        default: 'LISt'
    dsmdir:
        description:
            - Directory path where dsmadmc locates
        required: false
    sim_mode:
        description:
            - Used for playbook testing purposes together with sim_out and/or
              sim_rc.
              If set to true, the dsmadmc is not executed, but the module will
              provide the output set in sim_out and returncode set in sim_rc.
        required: false
        type: bool
        default: false
    sim_out:
        description:
            - Desired simulated output if sim_mode is set or executed in
              Check Mode ("Dry Run").
        required: false
    sim_rc:
        description:
            - Desired simulated returncode if sim_mode is set or executed in
              Check Mode ("Dry Run"). To have effect in Check Mode, sim_out must
              have a value.
        required: false
        type: int
        default: 0
extends_documentation_fragment:
    - azure
author:
    - Gabor Szobotka (@gszobotka)
'''

EXAMPLES = '''
# Run dsmadmc by selecting node domain
- name: Select node domain
  dsmadmc:
    command: SELECT domain_name FROM nodes where node_name=my_tsm_node
    se: mytsmserver1
    id: tsmadmin
    pa: tsm$3kr3tpass
    dsmdir: /usr/tivoli/tsm/client/ba/bin
# Simulate running dsmadmc
- name: Select node domain
  dsmadmc:
    command: SELECT domain_name FROM nodes where node_name=my_tsm_node
    se: mytsmserver1
    id: tsmadmin
    pa: tsm$3kr3tpass
    dsmdir: /usr/tivoli/tsm/client/ba/bin
    sim_mode: true
    sim_out: "This text will appear in result stdout"
    sim_rc: 2
'''

RETURN = '''
cmd:
  description: the command that was compiled and run/simulated on the remote machine
  returned: always
  type: str
  sample (based above example):
  /usr/tivoli/tsm/client/ba/bin/dsmadmc -SE=mytsmserver1 -ID=tsmadmin -PA=******** SELECT domain_name FROM nodes where node_name=my_tsm_node
sim_rc:
  description: sim_rc input argument
  returned: always
  type: int
  sample: 2
sim_out:
  description: sim_out input argument
  returned: always
  type: str
  sample: 'This text will appear in result stdout'
delta:
  description: cmd end time - cmd start time
  returned: always
  type: str
  sample: 0:00:00.001529
end:
  description: cmd end time
  returned: always
  type: str
  sample: '2017-09-29 22:03:48.084657'
start:
  description: cmd start time
  returned: always
  type: str
  sample: '2017-09-29 22:03:48.083128'
'''


import datetime
import glob
import os
import shlex

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.common.collections import is_iterable

def main():

    module = AnsibleModule(
        argument_spec=dict(
            command=dict(),
            serveraddress=dict(),
            se=dict(),
            id=dict(),
            password=dict(type='str', no_log=True),
            pa=dict(type='str', no_log=True),
            dataonly=dict(type='bool', default=False),
            commadelimited=dict(type='bool'),
            comma=dict(type='bool'),
            tabdelimited=dict(type='bool'),
            tab=dict(type='bool'),
            displaymode=dict(),
            displ=dict(),
            dsmdir=dict(type='path'),
            sim_mode=dict(type='bool', default=False),
            sim_out=dict(type='str'),
            sim_rc=dict(type='int')
        ),
        supports_check_mode=True
    )

    command = module.params['command']
    serveraddress = module.params['serveraddress']
    se = module.params['se']
    id = module.params['id']
    password = module.params['password']
    pa = module.params['pa']
    dataonly = module.params['dataonly']
    commadelimited = module.params['commadelimited']
    comma = module.params['comma']
    tabdelimited = module.params['tabdelimited']
    tab = module.params['tab']
    displaymode = module.params['displaymode']
    displ = module.params['displ']
    dsmdir = module.params['dsmdir']
    sim_mode = module.params['sim_mode']
    sim_out = module.params['sim_out']
    sim_rc = module.params['sim_rc']

    if not command or command.strip() == '':
        module.fail_json(rc=256, msg="no command given")

    if (not serveraddress or serveraddress.strip() == '') and (not se or se.strip() == ''):
        module.fail_json(rc=256, msg="no serveraddress given")
    elif serveraddress and se:
        module.fail_json(rc=256, msg="only serveraddress or se can be given, not both")
    else:
        serveraddress = serveraddress or se

    if not id or id.strip() == '':
        module.fail_json(rc=256, msg="no id given")

    if (not password) and (not pa):
        module.fail_json(rc=256, msg="no password given")
    elif password and pa:
        module.fail_json(rc=256, msg="only password or pa can be given, not both")
    else:
        password = password or pa

    if commadelimited and comma:
        module.fail_json(rc=256, msg="only commadelimited or comma can be given, not both")
    elif commadelimited or comma:
        commadelimited = commadelimited or comma

    if tabdelimited and tab:
        module.fail_json(rc=256, msg="only tabdelimited or tab can be given, not both")
    elif tabdelimited or tab:
        tabdelimited = tabdelimited or tab

    if displaymode and displ:
        module.fail_json(rc=256, msg="only displaymode or displ can be given, not both")
    elif displaymode or displ:
        displaymode = displaymode or displ


    # All args must be strings
    if is_iterable(command, include_strings=False):
        command = [to_native(arg, errors='surrogate_or_strict', nonstring='simplerepr') for arg in command]

    compiled_command = ""

    if dsmdir:
        if dsmdir.endswith("/"):
            compiled_command = dsmdir + "dsmadmc "
        else:
            compiled_command = dsmdir + "/" + "dsmadmc "
    else:
        compiled_command = "dsmadmc "
    if (dataonly and (str(dataonly).lower() == "yes" or str(dataonly).lower() == "true")):
        compiled_command += "-DATAONLY=YES "
    compiled_command += "-SE=" + serveraddress + " "
    compiled_command += "-ID=" + id + " "
    compiled_command += "-PA=" + password + " "
    if commadelimited:
        compiled_command += "-COMMA "
    if tabdelimited:
        compiled_command += "-TAB "
    if displaymode:
        compiled_command += "-DISPL=" + displaymode + " "
    compiled_command += "\"" + command +"\""



    startd = datetime.datetime.now()

    if not module.check_mode and not sim_mode:
        rc, out, err = module.run_command(compiled_command, encoding=None)
    elif (module.check_mode and sim_out) or sim_mode:
        if sim_out:
            out = sim_out
        else:
            out = ""
        if sim_rc:
            rc = sim_rc
        else:
            rc = 0
        err = ""
    else:
        module.exit_json(msg="skipped, running in check mode", skipped=True)

    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=compiled_command,
        stdout=out,
        stderr=err,
        rc=rc,
        sim_rc=sim_rc,
        sim_out=sim_out,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=True,
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
