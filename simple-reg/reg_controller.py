import magma as m
import hwtypes as ht
from main import rand_value, X, T


class Command(m.Enum):
    POWER_ON = 0
    BOOT = 1


RegInit = m.Receive[Command.POWER_ON, m.Receive[Command.BOOT, m.Epsilon]]


class RegController:
    def __init__(self):
        self.io = m.IO(command=m.In(Channel[RegInit]), curr_sum=m.In(T),
                       accum_input=m.In(T), accum_output=m.Out(T))
        self.accum = m.Register(T=T)
        self.X = X()
        self.io.accum @= self.accum.O

    def __call__(self):
        self.io.accum_output = self.X.O
        self.io.command.receive(Command.POWER_ON)

        self.io.accum_output = rand_value
        self.io.command.receive(Command.Boot)

        self.accum = self.io.curr_sum
        while True:
            yield
            self.accum = self.accum + self.io.accum_input
