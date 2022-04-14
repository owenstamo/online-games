from utilities import Vert
from gui import Gui, get_auto_center_function, GuiMouseEventHandler
import pygame

pygame.init()
canvas = pygame.display.set_mode((600, 450), pygame.RESIZABLE)
pygame.display.set_caption("Online games and all that jazz.")
clock = pygame.time.Clock()
canvas_active = True

main_menu = Gui.ContainerElement(Vert(0, 0), contents=[
    Gui.Rect(Vert(0, 100), Vert(50, 50), (0, 0, 0))])
# main_menu = Gui.BoundingContainer(Vert(0, 0), Vert(600, 450), contents=[
#     Gui.Rect(Vert(0, 100), Vert(50, 50), (0, 0, 0))])

main_menu.add_element(rect := Gui.Rect(Vert(50, 20), Vert(100, 50), (0, 0, 0), ignore_bounding_box=False))
rect.add_element(circ := Gui.Circle(Vert(100, 100), 50, (150, 150, 150), ignore_bounding_box=False))
circ.add_element(text := Gui.Text(Vert(0, 0), "OMG HI", 20, col=(255, 255, 255), text_align=("CENTER", "CENTER"),
                                  on_draw_before=get_auto_center_function(align=["CENTER", "CENTER"], offset_scaled_by_element=Vert(0, 0.075))))
rect.add_element(bar := Gui.Rect(Vert(0, -20), Vert(100, 20), (255, 255, 255),
                                 drag_parent=rect, drag_boundary=Vert(canvas.get_size())))

rect.add_element(button := Gui.Circle(Vert(0, -10), 10, (255, 255, 255)))
main_menu.add_element(Gui.Rect(Vert(200, 100), Vert(50, 50), (0, 0, 0)))

meh = GuiMouseEventHandler()

while canvas_active:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            canvas_active = False

    meh.main(main_menu)

    canvas.fill((215,) * 3)

    main_menu.draw(canvas)

    if main_menu.bounding_box:
        pygame.draw.circle(canvas, (100,) * 3, main_menu.bounding_box.top_left.list, 5)
        pygame.draw.circle(canvas, (100,) * 3, main_menu.bounding_box.bottom_right.list, 5)

    # circ.rad += 1
    # rect.size += Vert(2, 1) * 2
    # text.font_size += 1

    # print(main_menu.bounding_box)
    # print(main_menu.bounding_box[0], main_menu.bounding_box[1])

    clock.tick(60)
    pygame.display.flip()
