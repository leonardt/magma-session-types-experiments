import magma as m


@m.coroutine()
class RegController:
    def __init__(self):
        pass

    def __call__(self, advance: m.Bit) -> (m.Bit, m.Bit):
        while ~advance:
            yield m.bit(0), m.bit(0)
        yield m.bit(1), m.bit(0)
        while ~advance:
            yield m.bit(0), m.bit(0)
        yield m.bit(0), m.bit(1)
        while True:
            yield m.bit(0), m.bit(0)


if __name__ == "__main__":
    m.compile("build/RegController", RegController, inline=True)
