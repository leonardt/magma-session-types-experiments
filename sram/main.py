import magma as m


class SRAM(m.Circuit):
    io = m.IO(
        run_bisr=m.In(m.Bit),
        config_data_store=m.Producer(m.ReadyValid[m.Bits[32]]),
        config_data_load=m.Consumer(m.ReadyValid[m.Bits[32]]),
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
        en=m.In(m.Enable),
        CLK=m.Out(m.Clock)
    )


class GlobalController(m.Circuit):
    io = m.IO(
        clk_en=m.Out(m.Enable),
        sram_run_bisr=m.Out(m.Array[2, m.Bit]),
        arbiter_boot=m.Out(m.Bit),
        config_store_boot=m.Out(m.Bit)
    ) + m.ClockIO()


class Main(m.Circuit):
    io = m.ClockIO()
    gc = GlobalController()
    gc.CLK @= io.CLK

    clock_gen = ClockGenerator()
    clock_gen.en @= gc.clk_en

    arbiter = ConfigStoreArbiter()
    arbiter.CLK @= clock_gen.CLK
    arbiter.boot @= gc.arbiter_boot

    config_store = ConfigStore()
    config_store.boot @= gc.config_store_boot
    config_store.config_data_in @= arbiter.config_data_out[1]
    config_store.config_data_out @= arbiter.config_data_out[0]

    srams = [SRAM() for _ in range(2)]
    for i in range(2):
        srams[i].run_bisr @= gc.sram_run_bisr[i]
        arbiter.config_data_in[i][0] @= (
            srams[i].config_data_store)
        arbiter.config_data_in[i][1] @= (
            srams[i].config_data_load)
