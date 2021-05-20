import fault as f
import magma as m
import hwtypes as ht


T = m.UInt[8]


class X(m.Circuit):
    """
    Stub circuit to generate x, could add this as a magma/coreir primitive
    """
    io = m.IO(O=m.Out(T))
    verilog = "assign O = 'x;"


rand_value = ht.BitVector.random(8)


class AccumReg(m.Circuit):
    """
    `power_on` must be held high for one cycle, otherwise the output is x
    `boot` must be held high for one cycle **after** power_on, otherwise the
    contents of the register will be random
    """
    io = m.IO(power_on=m.In(m.Bit), boot=m.In(m.Bit), initial_sum=m.In(T),
              operation=m.In(m.Bit), accum_input=m.In(T), accum_output=m.Out(T)
              ) + m.ClockIO()
    accum_reg = m.Register(T, init=rand_value, reset_type=m.Reset)()
    # if boot is occuring, initialize the register value from external source
    # otherwise, sum the input with the register value
    accum_result = m.mux([accum_reg.O + io.accum_input,
                          accum_reg.O * io.accum_input], io.operation)
    accum_reg.I @= m.mux([accum_result,
                          io.initial_sum], io.boot)

    powered_on = m.Register(m.Bit, init=False)()
    powered_on.I @= m.mux([powered_on.O, 1], io.power_on)

    # When power_on happens, initialize register with random value (we do this
    # using reset logic)
    accum_reg.RESET @= m.reset(io.power_on)

    # If power is not on, output X, otherwise output register value
    io.accum_output @= m.mux([X().O, accum_reg.O], powered_on.O)


if __name__ == "__main__":
    tester = f.SynchronousTester(AccumReg)

    # Need to advance once to propogate values
    tester.advance_cycle()
    # Should be x initially
    tester.expect(AccumReg.accum_output, f.UnknownValue)
    tester.advance_cycle()
    tester.expect(AccumReg.accum_output, f.UnknownValue)

    # boot without power on should still be x
    tester.circuit.boot = 1
    tester.advance_cycle()
    tester.circuit.boot = 0
    tester.expect(AccumReg.accum_output, f.UnknownValue)

    # test power on sequence
    tester.circuit.power_on = 1
    tester.advance_cycle()
    tester.circuit.power_on = 0

    # Should no longer be x (instead random value, computed statically for
    # testing)
    tester.assert_(tester.circuit.accum_output != f.UnknownValue)
    tester.circuit.accum_output.expect(rand_value)

    # Check boot with curr sum set externally
    tester.circuit.boot = 1
    tester.circuit.initial_sum = initial_sum = ht.BitVector.random(8)
    tester.advance_cycle()
    tester.circuit.boot = 0
    tester.circuit.accum_output.expect(initial_sum)
    tester.circuit.operation = 0

    # Test sum functionality
    for _ in range(4):
        tester.circuit.accum_input = accum_amt = ht.BitVector.random(8)
        tester.advance_cycle()
        initial_sum += accum_amt
        tester.circuit.accum_output.expect(initial_sum)

    # test mul
    tester.circuit.operation = 1
    for _ in range(4):
        tester.circuit.accum_input = accum_amt = ht.BitVector.random(8)
        tester.advance_cycle()
        initial_sum *= accum_amt
        tester.circuit.accum_output.expect(initial_sum)

    # power on after boot should be random value
    tester.circuit.power_on = 1
    tester.advance_cycle()
    tester.circuit.power_on = 0
    tester.circuit.accum_output.expect(rand_value)

    # Need to use iverilog (versus verilator) for X support
    tester.compile_and_run("system-verilog", simulator="iverilog")
