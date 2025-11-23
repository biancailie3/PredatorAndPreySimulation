# PredatorAndPreySimulation

Predator-Prey Simulation
A real-time simulation of predator and prey dynamics in a 2D environment. This project models an ecosystem where predators hunt prey, and prey try to survive and reproduce, visualizing population dynamics over time.
Features
Agents: Predators and Prey with individual behaviors.
Movement: Agents move randomly and interact based on proximity.
Predation: Predators can catch prey if close enough.
Reproduction: Prey can reproduce, simulating population growth.
Visualization: Real-time graphical representation using pygame.
Statistics: Track and plot population changes over time.
User Interaction:
Add new predators or prey during simulation.
Toggle certain simulation parameters.

Controls
I – Add a new predator.
P – Add a new prey.
Q – Quit simulation.
Other keys can toggle parameters like speed or reproduction rate (if implemented).
How It Works
Prey move randomly and try to avoid predators.
Predators move randomly but chase nearby prey.
Each frame, agents update their position and interactions.
Population data is collected and plotted after the simulation ends using matplotlib.
