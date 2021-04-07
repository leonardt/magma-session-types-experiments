from hwtypes import BitVector
from session import Epsilon, Receive, Send, Offer, Choose, Dual, Channel
from check import check


ATMAuth = Offer[
    ("deposit", Receive[BitVector[32], Send[BitVector[32], Epsilon]]),
    ("withdraw", Receive[BitVector[32], Choose[("ok", Epsilon),
                                               ("err", Epsilon)]])
]

ATM = Receive[BitVector[32], Choose[("ok", ATMAuth), ("err", Epsilon)]]
Client = Dual(ATM)


def approved(id):
    return id < 4


balances = [100, 200, 300, 400]


def get_balance(id):
    return balances[id]


def set_balance(id, balance):
    balances[id] = balance


@check
def atm(c: Channel[ATM]):
    id = c.receive()
    if not approved(id):
        c.choose('err').close()
        return
    balance = get_balance(id)
    c.choose('ok')
    if c.offer("deposit"):
        amount = c.receive()
        balance += amount
        set_balance(id, balance)
        c.send(balance)
    # TODO: Would be nice if we could support else here
    elif c.offer("withdraw"):
        amount = c.receive()
        if balance >= amount:
            balance -= amount
            c.choose('ok')
        else:
            c.choose('err')
    c.close()


@check
def client(c: Channel[Client]):
    id = 2
    c.send(id)
    if c.offer("ok"):
        c.choose("withdraw")
        c.send(95)
        if c.offer("ok"):
            print("Withdraw succeeded")
        elif c.offer("err"):
            print("Insufficient funds")
    elif c.offer("err"):
        print("Invalid auth")
    c.close()
