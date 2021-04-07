from typing import TypeVar
import magma as m
import hwtypes as ht
from main import rand_value, X, T

from controller import controller, Receive, Epsilon, Channel, Rec, Choose


class Command(m.Enum):
    POWER_ON = 0
    BOOT = 1


AccumRegAbstract = Receive[Command.POWER_ON,
                           Receive[Command.BOOT, Epsilon]]
HoldLow = Rec("HoldLow", Receive[0, "HoldLow"])
PowerOnConcrete = Rec("PowerOnConcrete", Choose[(0, "PowerOnConcrete"),
                                                (1, HoldLow)])
T = m.Bits[8]
BootConcrete = Rec("BootConcrete", Choose[((T, 0), "BootConcrete"),
                                          ((T, 1), HoldLow)])


@controller
class RegController:
    def __call__(self,
                 abstract: Channel[AccumRegAbstract],
                 power_on: Channel[PowerOnConcrete],
                 boot: Channel[BootConcrete]):

        def wait_for_next_command():
            while ~abstract.receive():
                yield power_on.send(0), boot.send(0)

        yield from wait_for_next_command()
        yield power_on.send(1), boot.send(0)
        yield from wait_for_next_command()
        yield power_on.send(0), boot.send(1)
        while True:
            yield power_on.send(0), boot.send(0)
