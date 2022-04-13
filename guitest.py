from utilities import Vert
from gui import Gui, get_auto_center_function
import pygame

pygame.init()
canvas = pygame.display.set_mode((600, 450), pygame.RESIZABLE)
pygame.display.set_caption("Online games and all that jazz.")
clock = pygame.time.Clock()
canvas_active = True

main_menu = Gui.ContainerElement(Vert(0, 0), contents=[Gui.Rect(Vert(0, 100), Vert(50, 50), (0, 0, 0))])

print("adding rect!")

main_menu.add_element(rect := Gui.Rect(Vert(50, 0), Vert(50, 50), (0, 0, 0), ignore_bounding_box=True))
rect.add_element(circ := Gui.Circle(Vert(100, 100), 50, (150, 150, 150), ignore_bounding_box=False))
circ.add_element(text := Gui.Text(Vert(0, 0), "OMG HI", 20, col=(255, 255, 255), text_align=["CENTER", "CENTER"],
                                       on_draw_before=get_auto_center_function()))

# rect.reevaluate_bounding_box()

print(main_menu.bounding_box, "result!")

while canvas_active:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            canvas_active = False

    canvas.fill((215,) * 3)

    main_menu.draw(canvas)

    if main_menu.bounding_box:
        pygame.draw.circle(canvas, (100,) * 3, main_menu.bounding_box.top_left.list, 5)
        pygame.draw.circle(canvas, (100,) * 3, main_menu.bounding_box.bottom_right.list, 5)

    circ.rad += 1
    circ.pos += 1

    # print(main_menu.bounding_box)
    # print(main_menu.bounding_box[0], main_menu.bounding_box[1])

    clock.tick(60)
    pygame.display.flip()
