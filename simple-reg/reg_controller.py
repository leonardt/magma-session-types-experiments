import magma as m
import hwtypes as ht
from main import rand_value, X, T

from controller import controller, Receive, Epsilon, Channel, Rec


class Command(m.Enum):
    POWER_ON = 0
    BOOT = 1


class State(m.Enum):
    OFF = 0
    ON = 1
    BOOTED = 2


RegCtrl = Receive[Command.POWER_ON,
                  Receive[Command.BOOT,
                          Rec("valid", Send[T, "valid"])]]


@controller
class RegController:
    state: State

    def __call__(self, c: Channel[RegCtrl]):
        self.state = OFF

        c.receive(channel.POWER_ON)
        self.state = State.ON

        c.receive(channel.Boot)
        self.state = State.BOOTED

        c.close()
