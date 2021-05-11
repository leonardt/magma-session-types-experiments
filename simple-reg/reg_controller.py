import sys
sys.path.append("../session/")

from session import Receive, Epsilon, Channel, Rec, Choose
import magma as m


class Command(m.Enum):
    POWER_ON = 0
    BOOT = 1


RegCtrl = Receive[Command.POWER_ON,
                  Receive[Command.BOOT, Epsilon]]


@m.coroutine()
class RegController:
    def __init__(self):
        pass

    def __call__(self, valid: m.Bit, command: Command) -> (m.Bit, m.Bit):
        while ~valid | (command != Command.POWER_ON):
            yield m.bit(0), m.bit(0)
        yield m.bit(1), m.bit(0)
        while ~valid | (command != Command.BOOT):
            yield m.bit(0), m.bit(0)
        yield m.bit(0), m.bit(1)
        while True:
            yield m.bit(0), m.bit(0)


if __name__ == "__main__":
    m.compile("build/RegController", RegController, inline=True)
