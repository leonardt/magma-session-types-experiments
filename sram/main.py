import magma as m


class SRAM(m.Circuit):
    io = m.IO(
        run_bisr=m.In(m.Bit),
        config_data_store=m.Producer(m.ReadyValid[m.Bits[32]]),
        config_data_load=m.Consumer(m.ReadyValid[m.Bits[32]]),
        raddr=m.In(m.UInt[8]),
        rdata=m.Out(m.UInt[8]),
        waddr=m.In(m.UInt[8]),
        wdata=m.In(m.UInt[8]),
        wen=m.In(m.Enable)
    ) + m.ClockIO()


class ConfigStoreArbiter(m.Circuit):
    io = m.IO(
        config_data_in=m.Array[
            2,
            m.Tuple[
                m.Consumer(m.ReadyValid[m.Bits[32]]),
                m.Producer(m.ReadyValid[m.Bits[32]])
            ]
        ],
        config_data_out=m.Tuple[
            m.Consumer(m.ReadyValid[m.Bits[32]]),
            m.Producer(m.ReadyValid[m.Bits[32]])
        ],
        boot=m.In(m.Bit)
    ) + m.ClockIO()


class ConfigStore(m.Circuit):
    io = m.IO(
        config_data_in=m.Consumer(m.ReadyValid[m.Bits[32]]),
        config_data_out=m.Producer(m.ReadyValid[m.Bits[32]]),
        boot=m.In(m.Bit)
    ) + m.ClockIO()


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


class GlobalController(m.Circuit):
    io = m.IO(
        clk_gen_init=m.Out(m.Bit),
        sram_run_bisr=m.Out(m.Array[2, m.Bit]),
        arbiter_boot=m.Out(m.Bit),
        config_store_boot=m.Out(m.Bit)
    ) + m.ClockIO()


class Main(m.Circuit):
    io = m.ClockIO()
    gc = GlobalController()
    gc.CLK @= io.CLK

    clock_gen = ClockGenerator()
    clock_gen.CLK @= io.CLK
    clock_gen.init @= gc.clk_gen_init

    arbiter = ConfigStoreArbiter()
    arbiter.CLK @= clock_gen.clk_out
    arbiter.boot @= gc.arbiter_boot

    config_store = ConfigStore()
    config_store.CLK @= clock_gen.clk_out
    config_store.boot @= gc.config_store_boot
    config_store.config_data_in @= arbiter.config_data_out[1]
    config_store.config_data_out @= arbiter.config_data_out[0]

    srams = [SRAM() for _ in range(2)]
    for i in range(2):
        srams[i].run_bisr @= gc.sram_run_bisr[i]
        srams[i].CLK @= clock_gen.clk_out
        arbiter.config_data_in[i][0] @= (
            srams[i].config_data_store)
        arbiter.config_data_in[i][1] @= (
            srams[i].config_data_load)
        srams[i].raddr @= 0
        srams[i].waddr @= 0
        srams[i].wdata @= 0
        srams[i].wen @= False


m.compile("build/Main", Main)
