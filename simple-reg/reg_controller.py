import magma as m


@m.coroutine()
class RegController:
    def __init__(self):
        pass

    def __call__(self, config_en: m.Bit, config_data: m.Bit) -> (m.Bit, m.Bit):
        while ~config_en | (config_data != 0):
            yield m.bit(0), m.bit(0)
        yield m.bit(1), m.bit(0)
        while ~config_en | (config_data != 1):
            yield m.bit(0), m.bit(0)
        yield m.bit(0), m.bit(1)
        while True:
            yield m.bit(0), m.bit(0)


if __name__ == "__main__":
    m.compile("build/RegController", Regcontroller, inline=True)
