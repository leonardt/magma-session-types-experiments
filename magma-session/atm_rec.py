from hwtypes import BitVector
from session import Epsilon, Receive, Send, Offer, Choose, Dual, Rec


ATMAuth = Rec("ATMAuth", Offer[
    # L: Deposit
    Receive[BitVector[32], Send[BitVector[32], "ATMAuth"]],
    # R: Withdraw
    Receive[BitVector[32], Choose[Epsilon, "ATMAuth"]]
])

ATM = Receive[BitVector[32], Choose[ATMAuth, Epsilon]]
print(ATM)
print(Dual(ATM))
