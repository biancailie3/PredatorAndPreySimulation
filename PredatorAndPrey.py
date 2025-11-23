import pygame
import random
import math
import matplotlib.pyplot as plt

# ----------------- CONFIG -----------------
WIDTH, HEIGHT = 1000, 600
FPS = 60

# Colors
BACKGROUND_COLOR = (30, 30, 30)
PREY_COLOR = (255, 255, 0)
PREDATOR_COLOR = (255, 105, 180)
ENERGY_BAR_COLOR = (255, 0, 0)
FOOD_COLOR = (0, 255, 0)
OBSTACLE_COLOR = (100, 100, 100)
MATING_COLOR = (255, 200, 0)  # Color when mating

# Simulation parameters
PREY_COUNT = 25
PREDATOR_COUNT = 4
FOOD_COUNT = 40
OBSTACLE_COUNT = 5

MAX_TRAIL = 10
PREY_ENERGY_GAIN_FOOD = 30
PREY_ENERGY_LOSS = 0.03 
PREDATOR_ENERGY_GAIN_PREY = 60
PREDATOR_ENERGY_LOSS = 0.08  
PREY_REPRODUCE_ENERGY = 70
PREDATOR_REPRODUCE_ENERGY = 75
MATING_DURATION = 30  # timpi de oprire pt reproducere
MAX_FOOD_COUNT=25

FLOCKING = True


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

class Obstacle:
    def __init__(self):
        self.position = pygame.math.Vector2(random.uniform(50, WIDTH-50), random.uniform(50, HEIGHT-50))
         # X intre 50 si 750
         # Y intre 50 si 550
        self.radius = random.randint(20, 50) #raza obstacol
    def draw(self):
        pygame.draw.circle(screen, OBSTACLE_COLOR, (int(self.position.x), int(self.position.y)), self.radius)

class Food:
    def __init__(self, obstacles=None):
        # gasim pozitie valida sa nu se intersecteze cu obstacolele
        max_attempts = 50
        for _ in range(max_attempts):
            self.position = pygame.math.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
            valid = True
            #daca avem obstacole
            if obstacles:
                for obs in obstacles:
                    #distanta de la centrul obiectului la centrul obstacolului
                    if self.position.distance_to(obs.position) < obs.radius + 10:
                        valid = False
                        break
            if valid:
                break
        self.radius = 5
    def draw(self):
        pygame.draw.circle(screen, FOOD_COLOR, (int(self.position.x), int(self.position.y)), self.radius)

class Prey:
    def __init__(self, obstacles=None):
        # gasim pozitie valida sa nu se intersecteze cu obstacolele
        max_attempts = 50
        for _ in range(max_attempts):
            self.position = pygame.math.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
            valid = True
            if obstacles:
                for obs in obstacles:
                    if self.position.distance_to(obs.position) < obs.radius + 10:
                        valid = False
                        break
            if valid:
                break
        #dam random -1,1 ca sa poata sa mearga in toate directiile axei 360.
        self.velocity = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        #daca sta pe loc (adica lungime (viteza) = 0)
        if self.velocity.length() == 0:
            self.velocity = pygame.math.Vector2(1, 0)

        #normalizam ca sa aibe toti aceeasi viteza
        self.velocity = self.velocity.normalize()
        self.base_speed = 2.0
        self.speed = self.base_speed
        self.vision_radius = 80
        self.energy = random.randint(50, 100)
        self.trail = []
        self.mating_timer = 0
        self.mating_partner = None

    def update(self, predators, foods, preys, obstacles):
        if self.mating_timer > 0:
            self.mating_timer -= 1
              # daca se reproduce, sta pe loc mating_timer
            self.velocity = pygame.math.Vector2(0, 0)
            return
        
        # calculam flock_size pt speed boost in grup
        flock_size = 1
        for other in preys:
            if other != self and self.position.distance_to(other.position) < 50:
                flock_size += 1
        
        # calculam speed boost
        self.speed = self.base_speed * (1 + min(0.5, flock_size * 0.05))
        
        # calculam distanta fata de pradator ca sa fuga prey ul
        nearest_predator = None
        min_distance = self.vision_radius
        for predator in predators:
            distance = self.position.distance_to(predator.position)
            if distance < min_distance:
                min_distance = distance
                nearest_predator = predator
        if nearest_predator:
            #fuge de el cu viteza crescuta x1.5 in directia opusa de predator
            flee_direction = (self.position - nearest_predator.position).normalize()
            self.velocity = flee_direction * 1.5 

        # cauta partener daca au viata crescuta >70 si nu sunt pradatori in apropiere
        elif self.energy > PREY_REPRODUCE_ENERGY and not nearest_predator:
            nearest_mate = None
            min_mate_dist = 100
            for other in preys:
                #luam in considerare doar pe cei care nu sunt in proces de reproducere
                #si cautam cel mai apropiat (min_dist) prey de el 
                if other != self and other.energy > PREY_REPRODUCE_ENERGY and other.mating_timer == 0:
                    distance = self.position.distance_to(other.position)
                    if distance < min_mate_dist:
                        min_mate_dist = distance
                        nearest_mate = other
            
            if nearest_mate:
                #cream un vector de directie ca sa se indrepte spre el pt reproducere
                direction = (nearest_mate.position - self.position).normalize()
                self.velocity = direction * 0.8

        # Seek food if low energy
        elif self.energy < 60 and foods:
            nearest_food = min(foods, key=lambda f: self.position.distance_to(f.position))
            direction = (nearest_food.position - self.position).normalize()
            self.velocity = direction

        # Flocking

#alignment: directia medie a vecinilor 
#cohesion: tendinta de a se apropia de centrul vecinilor
#separation: de a nu se suprapune cu vecinii
#neighbor_count cati vecini sunt in raza de flocking

#verificam daca e activ(din buton) si daca avem un grup
        if FLOCKING and len(preys) > 1:
            alignment = pygame.math.Vector2(0,0)
            cohesion = pygame.math.Vector2(0,0)
            separation = pygame.math.Vector2(0,0)
            neighbor_count = 0
            for other in preys:
                if other == self:
                    continue
                distance = self.position.distance_to(other.position)
                if distance < 50:
                    alignment += other.velocity
                    cohesion += other.position
                    if distance > 0:
                        #forta de respingere
                        separation += (self.position - other.position) / distance
                    neighbor_count += 1
            if neighbor_count > 0:
                alignment /= neighbor_count
                cohesion = (cohesion/neighbor_count - self.position)
                separation /= neighbor_count
                #se modifica velocitatea unui prey in functie de parametrii ca sa faca flocking
                self.velocity += 0.05*alignment + 0.05*cohesion + 0.1*separation

        # evitam obstacolele
        for obs in obstacles:
            distance = self.position.distance_to(obs.position)
            if distance < obs.radius + 20:
                avoid_force = (self.position - obs.position).normalize() * 1.5
                self.velocity += avoid_force
#previne eroarea cand vectorul e 0
        if self.velocity.length() > 0:
            self.velocity = self.velocity.normalize()
        else:
            self.velocity = pygame.math.Vector2(1, 0)

        # calculeaza urmatoarea pozitie de miscare
        new_position = self.position + self.velocity * self.speed
        
        # verificam collision (daca se ciocneste de un obstacol)
        collision = False
        for obs in obstacles:
            if new_position.distance_to(obs.position) < obs.radius + 5:
                collision = True
                # aluneca pe marginea obstacolului daca e coliziune si isi schimba directia
                to_obstacle = obs.position - self.position
                if to_obstacle.length() > 0:
                    tangent = pygame.math.Vector2(-to_obstacle.y, to_obstacle.x).normalize()
                    self.velocity = tangent
                break
        
        if not collision:
            #daca nu e coliziune, prey isi muta pozitia normal
            self.position = new_position

        # pastram miscarea prey ului in limitele ferestrei
        self.position.x = max(0, min(self.position.x, WIDTH))
        self.position.y = max(0, min(self.position.y, HEIGHT))

        # actualizam "coada" prey ului ce contine pozitiile trecute ale acestuia
        self.trail.append(self.position.copy())
        if len(self.trail) > MAX_TRAIL:
            #daca lista de pozitii e prea lunga,stergem din pozitiile vechi
            self.trail.pop(0)

      
        self.energy -= PREY_ENERGY_LOSS

        # mananca daca e intr o raza mai mica de 10 si ii creste energia 
        for food in foods[:]:
            if self.position.distance_to(food.position) < 10:
                self.energy = min(100, self.energy + PREY_ENERGY_GAIN_FOOD)
                #mancarea dispare
                foods.remove(food)

    def draw(self):
        color = MATING_COLOR if self.mating_timer > 0 else PREY_COLOR
        if len(self.trail) > 1:
            pygame.draw.lines(screen, color, False, [(int(p.x), int(p.y)) for p in self.trail], 1)
        pygame.draw.circle(screen, color, (int(self.position.x), int(self.position.y)), 5)
        
        #enery bar pt prey
        if self.energy < 100:
            bar_width = 15
            bar_height = 3
            x = self.position.x - bar_width//2
            y = self.position.y - 10
            fill = max(0, (self.energy/100) * bar_width)
            pygame.draw.rect(screen, (50, 50, 0), (x, y, bar_width, bar_height))
            pygame.draw.rect(screen, (255, 255, 0), (x, y, fill, bar_height))

class Predator:
    def __init__(self, obstacles=None):
        # pozitionam pradatorul in afara obstacolelor
        max_attempts = 50
        for _ in range(max_attempts):
            self.position = pygame.math.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
            valid = True
            if obstacles:
                for obs in obstacles:
                    if self.position.distance_to(obs.position) < obs.radius + 10:
                        valid = False
                        break
            if valid:
                break
        
        angle = random.uniform(0, 2*math.pi)
        self.velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle))
        self.speed = 2.5  
        self.energy = random.randint(50, 100)
        self.trail = []
        self.mating_timer = 0
        self.mating_partner = None

    def update(self, preys, obstacles):
       #pierde energie pe parcursul timpului si moare dacae 0
        self.energy -= PREDATOR_ENERGY_LOSS
        if self.energy <= 0:
            return "dead"

        # daca e in reproducere, nu se misca cat timp e timer ul
        if self.mating_timer > 0:
            self.mating_timer -= 1
            self.velocity = pygame.math.Vector2(0, 0) #sta pe loc
            return

        # cauta partener daca are energie mare
        if self.energy > PREDATOR_REPRODUCE_ENERGY:
            nearest_mate = None
            min_mate_dist = 100
            for other in predators:
                if other != self and other.energy > PREDATOR_REPRODUCE_ENERGY and other.mating_timer == 0:
                    distance = self.position.distance_to(other.position)
                    if distance < min_mate_dist:
                        min_mate_dist = distance
                        nearest_mate = other
            
            if nearest_mate:
                direction = (nearest_mate.position - self.position).normalize()
                self.velocity = direction * 0.8

        # urmareste cel mai apropiat prey ( fara limita de distanta ), cauta non stop
        if preys:
            nearest_prey = min(preys, key=lambda p: self.position.distance_to(p.position))
            direction = (nearest_prey.position - self.position).normalize()
            self.velocity += direction * 0.7

        # evita obstacolele
        for obs in obstacles:
            distance = self.position.distance_to(obs.position)
            if distance < obs.radius + 20:
                avoid_force = (self.position - obs.position).normalize() * 1.2
                self.velocity += avoid_force

        if self.velocity.length() > 0:
            self.velocity = self.velocity.normalize()
        else:
            self.velocity = pygame.math.Vector2(1, 0)

        # generam pozitie noua de miscare
        new_position = self.position + self.velocity * self.speed
        
        # verificam daca se ciocneste de un obstacol
        collision = False
        for obs in obstacles:
            if new_position.distance_to(obs.position) < obs.radius + 8:
                collision = True
                to_obstacle = obs.position - self.position
                if to_obstacle.length() > 0:
                    tangent = pygame.math.Vector2(-to_obstacle.y, to_obstacle.x).normalize()
                    self.velocity = tangent
                break
        
        if not collision:
            self.position = new_position

        # dam update la "coada" cu pozitiile recente si stergem daca nu mai e loc
        self.trail.append(self.position.copy())
        if len(self.trail) > MAX_TRAIL:
            self.trail.pop(0)

    def draw(self):
        color = MATING_COLOR if self.mating_timer > 0 else PREDATOR_COLOR
        if len(self.trail) > 1:
            pygame.draw.lines(screen, color, False, [(int(p.x), int(p.y)) for p in self.trail], 1)
        
        angle = self.velocity.angle_to(pygame.math.Vector2(1,0)) if self.velocity.length() > 0 else 0
        points = [pygame.math.Vector2(10,0), pygame.math.Vector2(-5,-5), pygame.math.Vector2(-5,5)]
        rotated = [self.position + p.rotate(-angle) for p in points]
        pygame.draw.polygon(screen, color, rotated)

        # Energy bar pradator
        bar_width = 20
        bar_height = 4
        x = self.position.x - bar_width//2
        y = self.position.y - 20
        fill = max(0,(self.energy/100)*bar_width)
        pygame.draw.rect(screen,(80,0,0),(x,y,bar_width,bar_height))
        pygame.draw.rect(screen,ENERGY_BAR_COLOR,(x,y,fill,bar_height))


def draw_legend():
    font = pygame.font.SysFont(None, 22)
    screen.blit(font.render("Controls:", True, (200, 200, 200)), (10, 10))
    screen.blit(font.render("P - Add Prey", True, PREY_COLOR), (10, 30))
    screen.blit(font.render("O - Add Predator", True, PREDATOR_COLOR), (10, 50))
    screen.blit(font.render("F - Add Food", True, FOOD_COLOR), (10, 70))
    screen.blit(font.render("V - Toggle Flocking", True, (150, 150, 255)), (10, 90))
    screen.blit(font.render("B - Add Obstacle", True, OBSTACLE_COLOR), (10, 110))
    flocking_status = "ON" if FLOCKING else "OFF"
    screen.blit(font.render(f"Flocking: {flocking_status}", True, (255, 255, 255)), (10, 130))

def draw_stats(preys, predators, foods):
    font = pygame.font.SysFont(None, 24)
    screen.blit(font.render(f"Prey: {len(preys)}", True, (200, 200, 200)), (WIDTH-160, 10))
    screen.blit(font.render(f"Predator: {len(predators)}", True, (200, 200, 200)), (WIDTH-160, 30))
    screen.blit(font.render(f"Food: {len(foods)}", True, (200, 200, 200)), (WIDTH-160, 50))

# ----------------- Entitati initiale -----------------
obstacles = [Obstacle() for _ in range(OBSTACLE_COUNT)]
preys = [Prey(obstacles) for _ in range(PREY_COUNT)]
predators = [Predator(obstacles) for _ in range(PREDATOR_COUNT)]
foods = [Food(obstacles) for _ in range(FOOD_COUNT)]

# History tracking
history = {
    'preys': [], 
    'predators': [], 
    'foods': [],
    'prey_births': [],
    'predator_births': []
}

# Birth counters
prey_births_this_step = 0
predator_births_this_step = 0

# ----------------- MAIN LOOP -----------------
running = True
frame_count = 0

while running:
    clock.tick(FPS)
    screen.fill(BACKGROUND_COLOR)
    frame_count += 1
    
  
    prey_births_this_step = 0
    predator_births_this_step = 0

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                preys.append(Prey(obstacles))
            elif event.key == pygame.K_o:
                predators.append(Predator(obstacles))
            elif event.key == pygame.K_f:
                foods.append(Food(obstacles))
            elif event.key == pygame.K_v:
                FLOCKING = not FLOCKING
            elif event.key == pygame.K_b:
                obstacles.append(Obstacle())

    # Update entitati
    for prey in preys[:]:
        prey.update(predators, foods, preys, obstacles)
        #daca prey nu mai are energie, moare
        if prey.energy <= 0:
            preys.remove(prey)
        else:
            # cauta partener pt reproducere
            if prey.energy > PREY_REPRODUCE_ENERGY and prey.mating_timer == 0:
                for other in preys:
                    if other == prey or other.mating_timer > 0:
                        continue
                    if prey.position.distance_to(other.position) < 15 and other.energy > PREY_REPRODUCE_ENERGY:
                        # start imperechere
                        prey.mating_timer = MATING_DURATION
                        other.mating_timer = MATING_DURATION
                        prey.mating_partner = other
                        other.mating_partner = prey
                        
                        # se da nastere la un prey nou dupa imperechere
                        new_prey = Prey(obstacles)
                        new_prey.position = (prey.position + other.position) / 2
                        preys.append(new_prey)
                        #fiecare prey isi pierde 30 din energie dupa imperechere
                        prey.energy -= 30
                        other.energy -= 30
                        #crestem nasterile
                        prey_births_this_step += 1
                        break

    for predator in predators[:]:
        #dam remove la pradator daca nu mai are viata
        status = predator.update(preys, obstacles)
        if status == "dead":
            predators.remove(predator)
        else:
            # Reproducere
            if predator.energy > PREDATOR_REPRODUCE_ENERGY and predator.mating_timer == 0:
                for other in predators:
                    if other == predator or other.mating_timer > 0:
                        continue
                    if predator.position.distance_to(other.position) < 15 and other.energy > PREDATOR_REPRODUCE_ENERGY:
                        # Start reproducere
                        predator.mating_timer = MATING_DURATION
                        other.mating_timer = MATING_DURATION
                        predator.mating_partner = other
                        other.mating_partner = predator
                        #se naste un pradator nou
                        new_predator = Predator(obstacles)
                        new_predator.position = (predator.position + other.position) / 2
                        predators.append(new_predator)
                        #scade 35 din energie pt un pradator nou dupa imperechere
                        predator.energy -= 35
                        other.energy -= 35
                        predator_births_this_step += 1
                        break

    # Predator eats prey - remove prey si creste energia predator
    for predator in predators:
        for prey in preys[:]:
            if predator.position.distance_to(prey.position) < 10:
                preys.remove(prey)
                predator.energy = min(100, predator.energy + PREDATOR_ENERGY_GAIN_PREY)


    for obs in obstacles:
        obs.draw()
    for food in foods:
        food.draw()
    for prey in preys:
        prey.draw()
    for predator in predators:
        predator.draw()

    draw_legend()
    draw_stats(preys, predators, foods)

    # Update history
    history['preys'].append(len(preys))
    history['predators'].append(len(predators))
    history['foods'].append(len(foods))
    history['prey_births'].append(prey_births_this_step)
    history['predator_births'].append(predator_births_this_step)

    pygame.display.flip()

pygame.quit()

# ----------------- PLOTTING HISTORY -----------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

#populatie 
ax1.plot(history['preys'], label="Prey", color='yellow', linewidth=2)
ax1.plot(history['predators'], label="Predator", color='hotpink', linewidth=2)
ax1.plot(history['foods'], label="Food", color='green', linewidth=1, alpha=0.7)
ax1.set_xlabel("Time steps")
ax1.set_ylabel("Count")
ax1.set_title("Population Changes Over Time")
ax1.legend()
ax1.grid(True, alpha=0.3)

# birth rates
ax2.plot(history['prey_births'], label="Prey Births", color='gold', linewidth=2)
ax2.plot(history['predator_births'], label="Predator Births", color='deeppink', linewidth=2)
ax2.set_xlabel("Time steps")
ax2.set_ylabel("Births per timestep")
ax2.set_title("Birth Rates Over Time")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
