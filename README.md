# DCD - SCE Door Code Distribution

Every semester, new members join SCE as paid members expecting the perk of a door code, enabling access to the room at all hours. However, while the process of verifying membership is now significantly streamlined (shoutout 2026 Winter Interns), door code distribution was still painfully manual.
The department gives SCE a list of door codes for the members' entrance, and someone (usually our president) has to go through each one and manually assign a code to members who have to pester a poor, busy individual.

## BUT THAT ENDS HERE!
DCD is a simple, Python-based microservice that keeps and distributes door codes automatically when members are verified! This way, the only thing that must be done manually is the entry of the new door codes at the start of the semester - everything else is automated.

## How It Works
DCD stores door codes in a SQLite database and distributes them from a FastAPI server. While this is an extremely simple setup, the key functionality accomplished by DCD is even distribution of codes. There are far more members than there are door codes, so there is inevitably overlap. DCD uses a perfect blend of randomization and prioritization to make sure that every code has been used an equal amount of times before repeats, thus ensuring an even distribution.

DCD is then queried from [Clark](https://github.com/SCE-Development/Clark) when members make a membership payment, and their info is updated on their profile!
