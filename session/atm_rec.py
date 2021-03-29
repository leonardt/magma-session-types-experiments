from hwtypes import BitVector
from session import Epsilon, Receive, Send, Offer, Choose, Dual, Rec, Channel
from check import check


ATMAuth = Rec("ATMAuth", Offer[
    ("deposit", Receive[BitVector[32], Send[BitVector[32], "ATMAuth"]]),
    ("withdraw", Receive[BitVector[32], Choose[("ok", "ATMAuth"),
                                               ("err", Epsilon)]]),
    ("quit", Epsilon)
])

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
        c.choose('err')
        c.close()
    else:
        balance = get_balance(id)
        c.choose('ok')
        while True:
            if c.offer("deposit"):
                amount = c.receive()
                balance += amount
                set_balance(id, balance)
                c.send(balance)
            elif c.offer("withdraw"):
                amount = c.receive()
                if balance >= amount:
                    balance -= amount
                    c.choose('ok')
                else:
                    c.choose('err')
                    c.close()
                    return
            elif c.offer("quit"):
                c.close()
                return


@check
def client(c: Channel[Client]):
    id = 2
    c.send(id)
    if c.offer("ok"):
        c.choose("deposit")
        c.send(5)
        balance = c.receive()
        print(f"Deposit succeeded, balance={balance}")
        c.choose("withdraw")
        c.send(305)
        if c.offer("ok"):
            print("Withdraw succeeded")
            c.choose("quit")
        elif c.offer("err"):
            print("Insufficient funds")
    elif c.offer("err"):
        print("Invalid auth")
    c.close()
