from utilities import Vert
from gui import Gui
import pygame

pygame.init()
canvas = pygame.display.set_mode((600, 450), pygame.RESIZABLE)
pygame.display.set_caption("Online games and all that jazz.")
clock = pygame.time.Clock()
canvas_active = True

main_menu = Gui.ContainerElement(Vert(0, 0))

print("adding rect!")

main_menu.add_element(rect := Gui.Rect(Vert(50, 0), Vert(50, 50), (0, 0, 0)))

# rect.reevaluate_bounding_box()

print(main_menu.bounding_box, "result!")

while canvas_active:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            canvas_active = False

    canvas.fill((215,) * 3)

    for vert in main_menu.bounding_box:
        pygame.draw.circle(canvas, (100,) * 3, vert.list, 5)

    main_menu.draw(canvas)
    # print(main_menu.bounding_box)
    # print(main_menu.bounding_box[0], main_menu.bounding_box[1])


    clock.tick(60)
    pygame.display.flip()