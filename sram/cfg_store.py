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
    mem = m.Memory(2 ** 8, m.Bits[8])()
    mem.RADDR @= io.config_req.data.addr
    read_ctrl_state = m.Register(READ_CTRL_STATE)()
    io.config_req.ready @= read_ctrl_state.O == READ_CTRL_STATE.IDLE

    is_read_cmd = ((io.config_req.data.cmd == CONFIG_CMD.READ) &
                   io.config_req.valid)
    in_read_state = read_ctrl_state.O == READ_CTRL_STATE.READ
    read_ctrl_state.I @= m.mux(
        [
            # Transition to read state when valid read command
            m.bits(io.config_req.valid & is_read_cmd, 1),
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
                    io.config_req.valid)
    mem.WE @= is_write_cmd


if __name__ == "__main__":
    m.compile("build/ConfigStore", ConfigStore)
