from hwtypes import BitVector
from session import Epsilon, Receive, Send, Offer, Choose, Dual, Rec, Channel


ATMAuth = Rec("ATMAuth", Offer[
    ("deposit", Receive[BitVector[32], Send[BitVector[32], "ATMAuth"]]),
    ("withdraw", Receive[BitVector[32], Choose[("ok", "ATMAuth"),
                                               ("err", Epsilon)]]),
    ("quit", Epsilon)
])

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
    while True:
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
                c.left()
            else:
                c.right().close()
        elif choice == "exit":
            c.close()


def client(c: Channel[Client]):
    id = 2
    c.send(id)
    choice = c.offer()
    if choice == "ok":
        c.choose("deposit")
        c.send(5)
        choice = c.offer()
        if choice == "ok":
            print("Deposit succeeded")
        elif choice == "err":
            print("Insufficient funds")
        c.choose("withdraw")
        c.send(305)
        choice = c.offer()
        if choice == "ok":
            print("Withdraw succeeded")
        elif choice == "err":
            print("Insufficient funds")
    elif choice == "err":
        print("Invalid auth")
    c.close()
