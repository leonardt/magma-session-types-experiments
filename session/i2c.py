from hwtypes import BitVector
from session import Send, Receive, Choose, Epsilon, Channel
from check import check
import enum


class COND(enum.Enum):
    STOP = enum.auto()
    START = enum.auto()


I2CStop = Send[COND.STOP, Epsilon]
I2CWrite = Send[BitVector[8], I2CStop]
I2CRead = Receive[BitVector[8], I2CStop]
I2Ctrl = Send[COND.START, Send[BitVector[7], Choose[("read", I2CRead),
                                                    ("write", I2CWrite)]]]


@check
def i2c_controller(c: Channel[I2Ctrl]):
    c.send(COND.START)
    c.send(0xDE)
    c.choose("read")
    result = c.receive()
    c.send(COND.STOP)
    # bad = c.receive()
    c.close()
