from controller import Receive, Epsilon, Channel, controller, Send, Parallel
import magma as m
from hwtypes import BitVector, Bit


class Command(m.Enum):
    POWER_ON = 0
    BOOT = 1


RegID = m.Bits[2]
# Receive register ID, send initial sum and operation (add or mul)
RegCfg = Receive[RegID, Send[m.UInt[8], Send[m.Bit, Epsilon]]]
ConfigStore = Receive[Command.POWER_ON,
                      Receive[Command.BOOT,
                              Parallel[RegCfg, RegCfg]]]


# @controller()
class RegCfgController:
    def __init__(self):
        pass

    def __call__(self, chan: Channel[RegCfg], init: m.UInt[8], op: m.Bit) -> \
            m.Valid[m.Bits[2]]:
        id = chan.receive(wait_outputs1(m.Valid[m.Bits[2]](0, 0), ))
        yield m.Valid[m.Bits[2]](1, id)
        chan.send(init, wait_outputs=(m.Valid[m.Bits[2]](1, id), ))
        chan.send(op, wait_outputs=(m.Valid[m.Bits[2]](1, id), ))
        return m.Valid[m.Bits[2]](0, id)


# @controller()
class ConfigController:
    def __init__(self):
        pass

    def __call__(self, chan: Channel[ConfigStore]) -> \
            (m.Bit, m.Bit):
        chan.receive(Command.POWER_ON, wait_outputs=(m.bit(0), m.bit(0)))
        yield m.bit(1), m.bit(0)
        chan.receive(Command.BOOT, wait_outputs=(m.bit(0), m.bit(0)))
        yield m.bit(0), m.bit(1)
        ctrl0 = co_create(RegCfgController, name="ctrl0")
        ctrl1 = co_create(RegCfgController, name="ctrl1")
        co_await(ctrl0, ctrl1, wait_outputs=(m.bit(0), m.bit(0)))


class ConfigStore(m.Generator2):
    def __init__(self, num_regs):
        id_bits = m.bitutils.clog2(num_regs)
        self.io = io = m.IO(
            reg_ids=m.In(m.Array[2, m.Bits[id_bits]]),
            boot=m.In(m.Bit),
            power_on=m.In(m.Bit),
            reg_inits=m.Out(m.Array[2, m.Bits[8]]),
            reg_ops=m.Out(m.Array[2, m.Bit])
        ) + m.ClockIO()
        # TODO: We could add poweron/boot logic
        io.power_on.unused()
        io.boot.unused()

        reg_init_table = [BitVector.random(8) for _ in range(num_regs)]
        io.reg_inits @= m.array([
            m.mux(reg_init_table, io.reg_ids[i]) for i in range(2)
        ])

        reg_ops_table = [Bit.random() for _ in range(num_regs)]
        io.reg_ops @= m.array([
            m.mux(reg_ops_table, io.reg_ids[i]) for i in range(2)
        ])


if __name__ == "__main__":
    m.compile("ConfigStore", ConfigStore(2))
