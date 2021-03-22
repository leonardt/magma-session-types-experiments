class SessionTypeMeta(type):
    def __getitem__(cls, key):
        return cls(*key)

    def __repr__(cls):
        return cls.__name__


class SessionType(metaclass=SessionTypeMeta):
    pass


class Epsilon(SessionType):
    pass


class SessionTypeWithData(SessionType):
    def __init__(self, data_type, next):
        self.data_type = data_type
        self.next = next

    def __repr__(self):
        return f"{type(self).__name__}[{str(self.data_type)}, {str(self.next)}]"


class Receive(SessionTypeWithData):
    pass


class Send(SessionTypeWithData):
    pass


class SessionTypeWithBranch(SessionType):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        left_str = "\n    ".join(x for x in str(self.left).splitlines())
        right_str = "\n    ".join(x for x in str(self.right).splitlines())
        return f"{type(self).__name__}[\n    {left_str},\n    {right_str}\n]"


class Offer(SessionTypeWithBranch):
    pass


class Choose(SessionTypeWithBranch):
    pass


# TODO: Should this be parametrized like types or a function
def Dual(T):
    if isinstance(T, Offer):
        return Choose(Dual(T.left), Dual(T.right))
    if isinstance(T, Choose):
        return Offer(Dual(T.left), Dual(T.right))
    if isinstance(T, Send):
        return Receive(T.data_type, Dual(T.next))
    if isinstance(T, Receive):
        return Send(T.data_type, Dual(T.next))
    if T is Epsilon:
        return T
    if isinstance(T, Rec):
        return Rec(T.name, Dual(T.T))
    if isinstance(T, str):
        return T
    raise TypeError(f"Unsupport type {T}")


class Rec:
    def __init__(self, name, T):
        self.name = name
        self.T = T

    def __repr__(self):
        return f"Rec(\"{self.name}\", {self.T}"
