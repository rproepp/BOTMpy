# -*- coding: utf-8 -*-
#_____________________________________________________________________________
#
# Copyright (C) 2011 by Philipp Meier, Felix Franke and
# Berlin Institute of Technology
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#_____________________________________________________________________________
#
# Affiliation:
#   Bernstein Center for Computational Neuroscience (BCCN) Berlin
#     and
#   Neural Information Processing Group
#   School for Electrical Engineering and Computer Science
#   Berlin Institute of Technology
#   FR 2-1, Franklinstrasse 28/29, 10587 Berlin, Germany
#   Tel: +49-30-314 26756
#_____________________________________________________________________________
#
# Acknowledgements:
#   This work was supported by Deutsche Forschungs Gemeinschaft (DFG) with
#   grant GRK 1589/1
#     and
#   Bundesministerium für Bildung und Forschung (BMBF) with grants 01GQ0743
#   and 01GQ0410.
#_____________________________________________________________________________
#


"""ntrode interface

The NTrode is a container class provides a cyclic statemachine to apply
compute contexts to a homogeneous dataset. This way the same algorithm can be
applied to each part of the dataset with a consistent handling of input,
processing and output.
"""

__docformat__ = 'restructuredtext'
__all__ = ['NTrodeError', 'NTrode', 'NTrodeMemory']

##---IMPORTS

from multiprocessing import Process

##---CONSTANTS

_INP_HDL_ID = 0

##---CLASSES

class NTrodeError(Exception):
    pass


class NTrodeMemory(object):
    def reset(self):
        self.__dict__.clear()
        self.__init__()

    def __del__(self):
        self.__dict__.clear()

    def __str__(self, n=0):
        attr = [k for k in self.__dict__ if not k.startswith('_')]
        rval = ['{NTrodeMemory(%d)' % len(attr)]
        for k in attr:
            if isinstance(self.__dict__[k], NTrodeMemory):
                rval.append('%s%s : %s' % ('\t' * n,
                                           k,
                                           self.__dict__[k].__str__(n + 1)))
            else:
                rval.append('%s%s : %s' % ('\t' * n,
                                           k,
                                           str(self.__dict__[k])))
        rval.append('}')
        return '\n'.join(rval)


class NTrode(Process):
    """compute context container with parallelisation capability

    This class provides a container for NTrodeHandlers and will cycle its
    handlers for each item in the input set (which has to be generated by the
    input handler).
    """

    ## constructor

    def __init__(self, name=None, init_handlers=None, debug=False):
        """
        :Parameters:
            name : str
                name for this instance or None
            init_handlers : list
                list of handlers
            debug : bool
                debug toggle
        """

        # super
        super(NTrode, self).__init__(name=name)

        # state machine
        self._cur_state = 'OFF'
        self._states = {
            'OFF':(None, 'INIT'),
            'INIT':(self.initialise, 'INPUT'),
            'INPUT':(self.invoke_handlers, 'PROCESS'),
            'PROCESS':(self.invoke_handlers, 'OUTPUT'),
            'OUTPUT':(self.invoke_handlers, 'INPUT')
        }

        # NTrode memory namespace
        self.mem = NTrodeMemory()

        # handler list
        if init_handlers is None:
            raise ValueError('init_handlers is None!')
        self._handlers = None
        self.mem.init_handlers = init_handlers

        # members
        self.debug = debug

    ## publics methods

    def initialise(self):
        """public initialise interface"""

        # build and attach handlers
        self._handlers = []
        for item in self.mem.init_handlers:
            handler = item[0](**item[1])
            handler.attach(self)
            self._handlers.append(handler)

        # run custom initialisation
        self._initialise()

        # initialise handlers
        for item in self._handlers:
            item.initialise()

        if self.debug is True:
            print
            print self.mem
            print
            # raw_input('press a key to continue!')

    def finalise(self):
        """public finalization handler"""

        # finalise handlers
        if len(self._handlers) > 0:
            for item in self._handlers:
                item.finalise()

        # finalise self
        self._finalise()

    def reset(self):
        """public reset interface"""

        self._reset()
        self.mem.reset()
        self._cur_state = 'OFF'

    def invoke_handlers(self):
        """public handler invocation method"""

        # process each handlers context for this state
        # this processing is in order, so handler[0] should be the input
        # handler
        for item in self._handlers:
            item(self._cur_state)

    def cycle_engine(self):
        """process the cyclic state machine"""

        if self._cur_state in self._states:
            action, next = self._states[self._cur_state]
            if action is not None:
                action()
            self._cur_state = next
        else:
            raise RuntimeError('unknown state in ' + self)

    def run(self):
        """start the NTrode for automated operation

        this state-flow is started in a seperate process by calling self
        .start() or in the calling process by calling self.run()."""

        # go in statemachine mode
        while self._check_cycle_criterion() is True:
            self.cycle_engine()

        # finalise
        self.finalise()

    ## private methods

    def _initialise(self):
        pass

    def _finalise(self):
        pass

    def _reset(self):
        pass

    def _check_cycle_criterion(self):
        return True

##---MAIN

if __name__ == '__main__':
    pass
