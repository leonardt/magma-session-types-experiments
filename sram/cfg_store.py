import magma as m


class CONFIG_CMD(m.Enum):
    READ = 0
    WRITE = 1


ConfigData = m.Bits[8]


class ConfigReq(m.Product):
    addr = m.UInt[8]
    data = ConfigData
    cmd = CONFIG_CMD


class READ_CTRL_STATE(m.Enum):
    IDLE = 0
    READ = 1


class ConfigStore(m.Circuit):
    io = m.IO(
        config_req=m.Consumer(m.ReadyValid[ConfigReq]),
        config_resp=m.Producer(m.ReadyValid[ConfigData]),
        boot=m.In(m.Bit)
    ) + m.ClockIO()
    booted = m.Register(m.Bit)()
    booted.I @= io.boot | booted.O

    mem = m.Memory(2 ** 8, m.Bits[8])()
    mem.RADDR @= io.config_req.data.addr
    read_ctrl_state = m.Register(READ_CTRL_STATE)()
    io.config_req.ready @= read_ctrl_state.O == READ_CTRL_STATE.IDLE & booted.O

    is_read_cmd = ((io.config_req.data.cmd == CONFIG_CMD.READ) &
                   io.config_req.valid)
    in_read_state = read_ctrl_state.O == READ_CTRL_STATE.READ
    read_ctrl_state.I @= m.mux(
        [
            # Transition to read state when valid read command
            m.bits(io.config_req.valid & is_read_cmd & booted.O, 1),
            # Stay in read state until consumer is ready
            m.mux([READ_CTRL_STATE.READ, READ_CTRL_STATE.IDLE],
                  io.config_resp.ready)
        ],
        in_read_state
    )

    io.config_resp.data @= mem.RDATA
    io.config_resp.valid @= in_read_state

    mem.WADDR @= io.config_req.data.addr
    mem.WDATA @= io.config_req.data.data
    # TODO: We could add some delay here to make things interesting
    is_write_cmd = ((io.config_req.data.cmd == CONFIG_CMD.WRITE) &
                    io.config_req.valid & booted.O)
    mem.WE @= is_write_cmd


if __name__ == "__main__":
    import fault
    tester = fault.Tester(ConfigStore, ConfigStore.CLK)
    # Should not be ready until booted
    tester.circuit.config_req.ready.expect(0)
    tester.step(2)
    tester.circuit.boot = 1
    tester.step(2)
    tester.circuit.boot = 0
    tester.circuit.config_req.ready.expect(1)

    tester.circuit.config_req.data.addr = 0xDE
    tester.circuit.config_req.data.data = 0xAD
    tester.circuit.config_req.data.cmd = CONFIG_CMD.WRITE
    tester.circuit.config_req.valid = 1
    tester.step(2)

    tester.circuit.config_req.data.addr = 0xDE
    tester.circuit.config_req.data.cmd = CONFIG_CMD.READ
    tester.circuit.config_req.valid = 1
    tester.circuit.config_req.ready.expect(1)
    tester.step(2)
    # Should not be ready waiting for resp to be taken
    tester.circuit.config_req.ready.expect(0)
    tester.circuit.config_resp.valid.expect(1)
    tester.circuit.config_resp.data.expect(0xAD)
    tester.circuit.config_resp.ready = 1
    tester.step(2)
    tester.circuit.config_req.ready.expect(1)
    tester.circuit.config_resp.valid.expect(0)

    tester.compile_and_run("verilator")
