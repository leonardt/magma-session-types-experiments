from controller import Receive, Epsilon, Channel, controller, Send
import magma as m


class Command(m.Enum):
    POWER_ON = 0
    BOOT = 1


RegID = m.Bits[2]
# Receive register ID, send initial sum and operation (add or mul)
RegCfg = Receive[RegID, Send[m.UInt[8], Send[m.Bit, Epsilon]]]
ConfigStore = Receive[Command.POWER_ON,
                      Receive[Command.BOOT,
                              Parallel[RegCfg, RegCfg]]]
