# Copyright 2020 Pulser Development Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#from unittest.mock import patch

import numpy as np
import pytest

import qutip

from pulser import Sequence, Pulse, Register
from pulser.devices import Chadoq2
from pulser.waveforms import BlackmanWaveform
from pulser.simulation import Simulation

q_dict = {"control1": np.array([-4., 0.]),
          "target": np.array([0., 4.]),
          "control2": np.array([4., 0.])}
reg = Register(q_dict)
device = Chadoq2

duration = 3000
pi = Pulse.ConstantDetuning(BlackmanWaveform(duration, np.pi), 0., 0)
twopi = Pulse.ConstantDetuning(BlackmanWaveform(duration, 2*np.pi), 0., 0)
pi_Y = Pulse.ConstantDetuning(BlackmanWaveform(duration, np.pi), 0., -np.pi/2)

seq = Sequence(reg, Chadoq2)

# Declare Channels
seq.declare_channel('rydA', 'rydberg_local', 'control1')
seq.declare_channel('rydB', 'rydberg_local2', 'control2')
seq.declare_channel('raman', 'raman_local', 'control1')

d = 0  # Pulse Duration
t = 0  # Retarget time raman

# Prepare state 'hhh':
seq.add(pi_Y, 'raman')
d += 1
seq.target('target', 'raman')
t += 1
seq.add(pi_Y, 'raman')
d += 1
seq.target('control2', 'raman')
t += 1
seq.add(pi_Y, 'raman')
d += 1

prep_state = qutip.tensor([qutip.basis(3, 2) for _ in range(3)])

# Write CCZ sequence:
seq.add(pi, 'rydA', 'wait-for-all')  # Wait for state preparation to finish.
d += 1
seq.align('rydA', 'rydB')
seq.add(pi, 'rydB')
d += 1
seq.target('target', 'rydA')
seq.align('rydA', 'rydB')
seq.add(twopi, 'rydA')
d += 1
seq.align('rydA', 'rydB')
seq.add(pi, 'rydB')
d += 1
seq.target('control1', 'rydA')
seq.align('rydA', 'rydB')
seq.add(pi, 'rydA')
d += 1


def test_init():
    fake_sequence = {'pulse1': 'fake', 'pulse2': "fake"}
    with pytest.raises(TypeError, match='sequence has to be a valid'):
        Simulation(fake_sequence)
    sim = Simulation(seq)
    assert sim._seq == seq
    assert sim._qdict == seq.qubit_info
    assert sim._size == len(seq.qubit_info)
    assert sim._tot_duration == (duration * d
                                 + seq._channels['raman'].retarget_time * t)
    assert sim._qid_index == {"control1": 0, "target": 1, "control2": 2}
