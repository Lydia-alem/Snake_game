import cv2
import pygame
import random
import sys
import threading
from cvzone.HandTrackingModule import HandDetector

#-------------- HAND TRACKER Class--------

class HandTracker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)
        self.cap.set(4, 480)

        self.detector = HandDetector(maxHands=1, detectionCon=0.7)
        self.direction = "RIGHT"
        self.running = True
        self.threshold = 70

    def run(self):
        while self.running:
            success, frame = self.cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)
            hands, frame = self.detector.findHands(frame)

            h, w, _ = frame.shape
            cx, cy = w // 2, h // 2

            # center lines
            cv2.line(frame, (cx, 0), (cx, h), (200, 200, 200), 1)
            cv2.line(frame, (0, cy), (w, cy), (200, 200, 200), 1)

            if hands:
                hand = hands[0]
                lmList = hand["lmList"]

                # Index finger tip (landmark 8)
                ix, iy = lmList[8][0], lmList[8][1]

                dx = ix - cx
                dy = iy - cy

                if abs(dx) > abs(dy):
                    if dx > self.threshold:
                        self.direction = "RIGHT"
                    elif dx < -self.threshold:
                        self.direction = "LEFT"
                else:
                    if dy > self.threshold:
                        self.direction = "DOWN"
                    elif dy < -self.threshold:
                        self.direction = "UP"

                cv2.circle(frame, (ix, iy), 10, (0, 255, 0), -1)

            cv2.putText(frame, f"Direction: {self.direction}",
                        (20, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        1.3, (0, 255, 255), 3)

            cv2.imshow("🎮 Hand Control (ESC to quit)", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                self.stop()

        self.cap.release()
        cv2.destroyAllWindows()

    def stop(self):
        self.running = False



# ----SNAKE GAME-------

class SnakeGame:
    def __init__(self, tracker):
        pygame.init()
        self.WIDTH, self.HEIGHT = 800, 600
        self.CELL = 20
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("🐍 Hand Controlled Snake (cvzone)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 28, bold=True)
        self.tracker = tracker

        self.SNAKE_COLOR = (50, 255, 120)
        self.FOOD_COLOR = (255, 80, 80)
        self.BG_COLOR = (20, 20, 50)

    def random_food(self):
        return [
            random.randrange(0, self.WIDTH, self.CELL),
            random.randrange(0, self.HEIGHT, self.CELL)
        ]

    def game_loop(self):
        snake_pos = [400, 300]
        snake_body = [list(snake_pos)]
        direction = "RIGHT"
        food_pos = self.random_food()
        score = 0
        speed = 10

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.tracker.stop()
                    pygame.quit()
                    sys.exit()

            # Hand direction
            new_dir = self.tracker.direction
            opposite = {"UP":"DOWN","DOWN":"UP","LEFT":"RIGHT","RIGHT":"LEFT"}
            if new_dir != opposite.get(direction):
                direction = new_dir

            # Move snake
            if direction == "UP":
                snake_pos[1] -= self.CELL
            elif direction == "DOWN":
                snake_pos[1] += self.CELL
            elif direction == "LEFT":
                snake_pos[0] -= self.CELL
            elif direction == "RIGHT":
                snake_pos[0] += self.CELL

            # Wrap screen
            snake_pos[0] %= self.WIDTH
            snake_pos[1] %= self.HEIGHT

            snake_body.insert(0, list(snake_pos))

            # Eat food
            if snake_pos == food_pos:
                score += 1
                food_pos = self.random_food()
                speed = min(20, speed + 0.5)
            else:
                snake_body.pop()

            # Collision with itself
            if snake_pos in snake_body[1:]:
                running = False

            # Draw
            self.screen.fill(self.BG_COLOR)

            for i, segment in enumerate(snake_body):
                shade = max(80, 255 - i * 6)
                pygame.draw.rect(
                    self.screen,
                    (50, shade, 120),
                    (*segment, self.CELL, self.CELL),
                    border_radius=6
                )

            pygame.draw.rect(
                self.screen,
                self.FOOD_COLOR,
                (*food_pos, self.CELL, self.CELL),
                border_radius=6
            )

            score_text = self.font.render(f"Score: {score}", True, (255,255,255))
            dir_text = self.font.render(f"Direction: {direction}", True, (200,200,255))

            self.screen.blit(score_text, (20, 20))
            self.screen.blit(dir_text, (20, 60))

            pygame.display.update()
            self.clock.tick(speed)

        self.game_over()

    def game_over(self):
        self.screen.fill((10, 10, 40))
        over = self.font.render("GAME OVER", True, (255, 80, 80))
        info = self.font.render("Press R to Restart | Q to Quit", True, (200,200,200))

        self.screen.blit(over, (self.WIDTH//2 - 100, self.HEIGHT//2 - 40))
        self.screen.blit(info, (self.WIDTH//2 - 200, self.HEIGHT//2 + 10))
        pygame.display.update()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.tracker.stop()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.game_loop()
                    elif event.key == pygame.K_q:
                        self.tracker.stop()
                        pygame.quit()
                        sys.exit()



# ------------RUN---------------

if __name__ == "__main__":
    tracker = HandTracker()
    tracker.start()

    game = SnakeGame(tracker)
    game.game_loop()

    tracker.stop()
