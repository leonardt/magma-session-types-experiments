import magma as m
import fault as f
from accum_reg import AccumReg, rand_value
from reg_controller import RegController


@m.coroutine()
class MainController:
    def __init__(self):
        pass

    def __call__(self, config_en: m.Bit, config_data: m.Bit) -> \
            (m.Bit, m.Bits[1]):
        while ~config_en | (config_data != 0):
            yield m.bit(0), m.bits(0, 1)
        yield m.bit(1), m.bits(0, 1)
        while ~config_en | (config_data != 1):
            yield m.bit(0), m.bits(0, 1)
        yield m.bit(1), m.bits(1, 1)
        while True:
            yield m.bit(0), m.bits(0, 1)


class Main(m.Circuit):
    io = m.IO(
        config_en=m.In(m.Bit),
        config_data=m.In(m.Bit),
        accum_output=m.Out(m.UInt[8])
    ) + m.ClockIO()

    accum_reg = AccumReg()
    main_controller = MainController()
    reg_controller = RegController()
    main_controller.config_en @= io.config_en
    main_controller.config_data @= io.config_data
    reg_controller.valid @= main_controller.O0
    reg_controller.command @= main_controller.O1
    accum_reg.power_on @= reg_controller.O0
    accum_reg.boot @= reg_controller.O1
    # Hard code value
    accum_reg.accum_input @= 1
    accum_reg.curr_sum @= 0xDE
    io.accum_output @= accum_reg.accum_output


if __name__ == "__main__":
    tester = f.SynchronousTester(Main)
    tester.zero_inputs()
    # Need to advance once to propogate values
    tester.advance_cycle()
    # Should be x initially
    tester.expect(AccumReg.accum_output, f.UnknownValue)
    tester.advance_cycle()
    tester.expect(AccumReg.accum_output, f.UnknownValue)

    # boot without power on should still be x
    tester.circuit.config_en = 1
    tester.circuit.config_data = 1
    tester.advance_cycle()
    tester.circuit.config_en = 0
    tester.expect(AccumReg.accum_output, f.UnknownValue)

    # test power on sequence
    tester.circuit.config_en = 1
    tester.circuit.config_data = 0
    tester.advance_cycle()
    tester.circuit.config_en = 0

    # Should no longer be x (instead random value, computed statically for
    # testing)
    tester.assert_(tester.circuit.accum_output != f.UnknownValue)
    tester.circuit.accum_output.expect(rand_value)

    # Check boot with curr sum set externally
    tester.circuit.config_en = 1
    tester.circuit.config_data = 1
    tester.advance_cycle()
    tester.circuit.config_en = 0
    curr_sum = 0xDE
    tester.circuit.accum_output.expect(curr_sum)

    # Test sum functionality
    for _ in range(4):
        tester.advance_cycle()
        curr_sum += 1
        tester.circuit.accum_output.expect(curr_sum)

    # Need to use iverilog (versus verilator) for X support
    tester.compile_and_run("system-verilog", simulator="iverilog")
