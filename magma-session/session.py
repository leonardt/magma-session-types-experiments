class SessionType:
    pass


class Epsilon(SessionType):
    pass


class WithData:
    def __init__(self, data_type):
        self.data_type = data_type


class Receive(SessionType, WithData):
    pass


class Send(SessionType, WithData):
    pass


class WithBranch:
    def __init__(self, left, right):
        self.left = left
        self.right = right


class Offer(SessionType):
    pass
