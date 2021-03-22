from hwtypes import BitVector
from session import Epsilon, Receive, Send, Offer, Choose, Dual


ATMAuth = Offer[
    # L: Deposit
    Receive[BitVector[32], Send[BitVector[32], Epsilon]],
    # R: Withdraw
    Receive[BitVector[32], Choose[Epsilon, Epsilon]]
]

ATM = Receive[BitVector[32], Choose[ATMAuth, Epsilon]]
print(ATM)
print(Dual(ATM))
