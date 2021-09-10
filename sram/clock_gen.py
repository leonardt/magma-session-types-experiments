import magma as m


class ClockGenerator(m.Circuit):
    io = m.IO(
        init=m.In(m.Bit),
        clk_out=m.Out(m.Clock)
    ) + m.ClockIO()
    en = m.Register(m.Bit)()
    en.I @= en.O | io.init
    tff = m.Register(m.Bit, has_enable=True)()
    tff.CE @= en.O
    tff.I @= tff.O ^ 1
    io.clk_out @= m.clock(tff.O)


if __name__ == "__main__":
    import fault as f
    tester = f.Tester(ClockGenerator, ClockGenerator.CLK)
    tester.circuit.init = 0
    for i in range(3):
        tester.step(2)
        tester.expect(ClockGenerator.clk_out, 0)
    tester.circuit.init = 1
    tester.step(2)
    tester.circuit.init = 0
    tester.step(2)
    for i in range(6):
        tester.step(2)
        tester.expect(ClockGenerator.clk_out, i % 2)
    tester.compile_and_run(target="verilator")
