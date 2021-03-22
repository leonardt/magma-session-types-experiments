class SessionTypeMeta(type):
    def __getitem__(cls, key):
        return cls(*key)


class SessionType(metaclass=SessionTypeMeta):
    pass


class Epsilon(SessionType):
    pass


class SessionTypeWithData(SessionType):
    def __init__(self, data_type, next):
        self.data_type = data_type
        self.next = next


class Receive(SessionTypeWithData):
    pass


class Send(SessionTypeWithData):
    pass


class SessionTypeWithBranch(SessionType):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class Offer(SessionTypeWithBranch):
    pass


class Choose(SessionTypeWithBranch):
    pass
