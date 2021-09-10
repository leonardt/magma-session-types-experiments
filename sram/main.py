import magma as m
from clock_gen import ClockGenerator
from cfg_store import ConfigStore, ConfigReq, ConfigData
from cfg_store_arb import ConfigStoreArbiter


class SRAM(m.Circuit):
    io = m.IO(
        run_bisr=m.In(m.Bit),
        config_req=m.Producer(m.ReadyValid[ConfigReq]),
        config_resp=m.Consumer(m.ReadyValid[ConfigData]),
        raddr=m.In(m.UInt[8]),
        rdata=m.Out(m.UInt[8]),
        waddr=m.In(m.UInt[8]),
        wdata=m.In(m.UInt[8]),
        wen=m.In(m.Enable)
    ) + m.ClockIO()


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
    config_store.config_req @= arbiter.config_tx_out[0]
    config_store.config_resp @= arbiter.config_tx_out[1]

    srams = [SRAM() for _ in range(2)]
    for i in range(2):
        srams[i].run_bisr @= gc.sram_run_bisr[i]
        srams[i].CLK @= clock_gen.clk_out
        arbiter.config_tx_in[i][0] @= (
            srams[i].config_req)
        arbiter.config_tx_in[i][1] @= (
            srams[i].config_resp)
        srams[i].raddr @= 0
        srams[i].waddr @= 0
        srams[i].wdata @= 0
        srams[i].wen @= False


m.compile("build/Main", Main)
