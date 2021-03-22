from hwtypes import BitVector
from session import (Epsilon, Receive, Send, Offer, Choose, Dual, Channel,
                     Branch)


ATMAuth = Offer[
    ("deposit", Receive[BitVector[32], Send[BitVector[32], Epsilon]]),
    ("withdraw", Receive[BitVector[32], Choose[("ok", Epsilon),
                                               ("err", Epsilon)]])
]

ATM = Receive[BitVector[32], Choose[("ok", ATMAuth), ("err", Epsilon)]]
print(ATM)
print(Dual(ATM))


def approved(id):
    return id < 4


balances = [100, 200, 300, 400]


def get_balance(id):
    return balances[id]


def set_balance(id, balance):
    balances[id] = balance


def atm(c: Channel[ATM]):
    id = c.receive()
    if not approved(id):
        c.right.close()
        return
    balance = get_balance(id)
    c.left()
    choice = c.offer()
    if choice == "deposit":
        amount = c.receive()
        balance += amount
        set_balance(id, balance)
        c.send(balance)
    elif choice == "withdraw":
        amount = c.receive()
        if balance >= amount:
            balance -= amount
            c.left().close()
        else:
            c.right().close()
