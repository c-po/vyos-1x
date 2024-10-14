# Copyright 2024 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

"""
Library used to interface with FRRs mgmtd introduced in version 10.0
"""

import os

from vyos.utils.file import write_file
from vyos.utils.process import cmd
from vyos.template import render_to_string

DEBUG_ON = os.path.exists('/tmp/vyos.frr.debug')

def debug(message):
    if not DEBUG_ON:
        return
    print(message)

class FRRender:
    def __init__(self):
        ppid = os.getppid()
        self._frr_conf = f'/tmp/vyos.frr.{ppid}'

    def generate(self, config):
        if not isinstance(config, dict):
            raise ValueError('config must be of type dict')

        if DEBUG_ON:
            import pprint
            pprint.pprint(config)

        debug('======< RENDERING CONFIG >======')
        # we can not reload an empty file, thus we always embed the marker
        output = '!\n'
        if 'bgp' in config:
            output += render_to_string('frr/bgpd.frr.j2', config['bgp']) + '\n'
        if 'ospf' in config:
            output += render_to_string('frr/ospfd.frr.j2', config['ospf']) + '\n'
        if 'ospfv3' in config:
            output += render_to_string('frr/ospf6d.frr.j2', config['ospfv3']) + '\n'
        if 'policy' in config:
            output += render_to_string('frr/policy.frr.j2', config['policy']) + '\n'
        if 'rip' in config:
            output += render_to_string('frr/ripd.frr.j2', config['rip']) + '\n'
        if 'ripng' in config:
            output += render_to_string('frr/ripngd.frr.j2', config['ripng']) + '\n'
        if 'vrf' in config and 'name' in config['vrf']:
            output += render_to_string('frr/zebra.vrf.route-map.frr.j2', config['vrf']) + '\n'
            for vrf, vrf_config in config['vrf']['name'].items():
                print(vrf, vrf_config)
                if 'protocols' in vrf_config and 'ospf' in vrf_config['protocols']:
                    vrf_config['protocols']['ospf']['vrf'] = vrf
                    output += render_to_string('frr/ospfd.frr.j2', vrf_config['protocols']['ospf']) + '\n'

        debug(output)
        debug('======< RENDERING CONFIG COMPLETE >======')
        write_file(self._frr_conf, output)

    def apply(self):
        cmdline = '/usr/lib/frr/frr-reload.py --reload'
        if DEBUG_ON:
            cmdline += ' --debug'

        cmd(f'{cmdline} {self._frr_conf}')
        debug('======< DONE APPLYING CONFIG  >======')

        #if os.path.exists(self._frr_conf):
        #    os.unlink(self._frr_conf)

    def save_configuration():
        """ T3217: Save FRR configuration to /run/frr/config/frr.conf """
        return cmd('/usr/bin/vtysh -n -w')
