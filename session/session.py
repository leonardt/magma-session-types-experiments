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
        name_str = type(self).__name__
        return f"{name_str}[{str(self.data_type)}, {str(self.next)}]"


class Receive(SessionTypeWithData):
    pass


class Send(SessionTypeWithData):
    pass


class SessionTypeWithBranches(SessionType):
    def __init__(self, *branches):
        self.branches = branches

    def __repr__(self):
        branches = ["\n    ".join(x for x in str(y).splitlines())
                    for y in self.branches]
        branches = "\n    ".join(branches)
        return f"{type(self).__name__}[\n    {branches}\n]"


class Offer(SessionTypeWithBranches):
    pass


class Choose(SessionTypeWithBranches):
    pass


# TODO: Should this be parametrized like types or a function
def Dual(T):
    if isinstance(T, Offer):
        return Choose(*((x[0], Dual(x[1])) for x in T.branches))
    if isinstance(T, Choose):
        return Offer(*((x[0], Dual(x[1])) for x in T.branches))
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
        return f"Rec(\"{self.name}\", {self.T})"


class ChannelMeta(type):
    def __getitem__(cls, T):
        return cls(T)


class Channel(metaclass=ChannelMeta):
    def __init__(self, T):
        self.T = T


class Parallel(SessionType):
    def __init__(self, *Ts):
        self.Ts = Ts

    def __repr__(self):
        return f"Parallel({', '.join(str(t) for t in self.Ts)})"
