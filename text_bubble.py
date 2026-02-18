import copy

from PIL import Image, ImageDraw, ImageFont
from clipseg import get_location
from character import CharacterMoment, Character
from frame import Frame
import math
from textwrap3 import fill

MAX_TEXT_WIDTH =100

font_size = 30
font = ImageFont.truetype("NotoSansArabic-Medium.ttf", font_size)
sample_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzçàèéíïòóúü"
bbox = font.getbbox(sample_text)
CHAR_WIDTH = (bbox[2] - bbox[0]) / len(sample_text)
MAX_HEIGHT = 100


def pick_relative_location(image: Image, head_location, t_width, t_height):
    """
    Picks a location relative to the head location
    If the head is on the left side of the image, the text bubble will be on the right side
    If the head is on the right side of the image, the text bubble will be on the left side
    Ensures that there is enough room for the text bubble to fit without going off the image
    :param image: PIL Image
    :param head_location: A tuple of (x, y) coordinates
    :return: A tuple of (x, y) coordinates to define the top left corner of the text bubble
    """

    # Get the size of the image
    image_size = image.size
    image_width = image_size[0]
    image_height = image_size[1]

    # Get the head location
    head_x = head_location[0]
    head_y = head_location[1]

    # If the head is on the left side of the image, the text bubble will be on the right side
    if head_x < image_width / 2:
        x = head_x - 60 - t_width
    # If the head is on the right side of the image, the text bubble will be on the left side
    else:
        x = head_x + 60

    # Placing the bubble above the head
    # If the bubble would go off the top of the image, place it as high as possible
    y = head_y - 60 - t_height
    if y < MAX_HEIGHT:
        y = 0

    return x, y


def calculate_text_size(text: str, font):
    lines = text.split("\n")

    # Finding the line that is the widest bbox
    longest_line_width = 0
    for line in lines:
        bbox = font.getbbox(line)
        longest_line_width = max(longest_line_width, bbox[2] - bbox[0])


    bbox = font.getbbox(lines[0])
    single_line_height = bbox[3] - bbox[1]
    return longest_line_width, (single_line_height + single_line_height / 6) * len(lines)


def wrap_text(text: str, max_width=MAX_TEXT_WIDTH):
    """
    Wraps text to a certain width
    :param text: The text to be wrapped (i.e. adding newlines)
    :param max_width: The maximum width of the text in pixels
    :return: The same text with newlines added to wrap the text
    """
    bbox_if_single_line = font.getbbox(text)
    # Average character width
    char_width = (bbox_if_single_line[2] - bbox_if_single_line[0]) / len(text)

    text = fill(text, width=int(max_width / char_width))

    return text


def find_head_edge(image: Image, head_location, logits):
    """
    Finds the edge of the head
    :param image: PIL Image
    :param head_location: A tuple of (x, y) coordinates
    :param logits: The logits from the CLIPSeg model
    :return: A tuple of (x, y) coordinates
    """
    # Get the size of the image
    image_size = image.size
    image_width = image_size[0]
    image_height = image_size[1]

    # Get the head location
    head_x = head_location[0]
    head_y = head_location[1]

    head_logit = logits[int(head_y)][int(head_x)]
    if head_x < image_width / 2:
        direction = -1
    else:
        direction = 1

    # Find the edge of the head
    check_x = head_x
    check_y = head_y
    while 0 <= check_x < image_width and 0 <= check_y < image_height:
        check_logit = logits[int(check_y)][int(check_x)]
        if check_logit < head_logit - abs(head_logit * 0.1):
            break
        check_x += direction * 2
        check_y -= 0.1

    return check_x, check_y


class TextBubble:
    def __init__(self, loc, width, height, point_to_loc, text, head_loc):
        """
        Holds all the values associated with a text bubble
        :param loc: The top left corner of the ellipse (x,y)
        :param width: How wide the ellipse is
        :param height: How tall the ellipse is
        :param point_to_loc: The location that the triangle points to (x,y)
        :param text: The text to be displayed in the bubble
        """

        self.head_loc = head_loc
        self.loc = loc
        self.width = width
        self.height = height
        self.point_to_loc = point_to_loc  # Head edge
        self.text = text

    def get_off_of_point_to_loc(self):
        """
        If point to loc is within the bubble or near being within the bubble, move the bubble away from it
        """
        pad = 100

        while self.loc[1] - pad < self.point_to_loc[1] < self.loc[1] + self.height + pad:
            angle = math.atan2(self.point_to_loc[1] - self.loc[1], self.point_to_loc[0] - self.loc[0])
            self.loc = (self.loc[0] - math.cos(angle) * 10, self.loc[1] - 40 * math.sin(angle))
            if math.sin(angle) == 0:
                self.loc = (self.loc[0], self.loc[1] + 40)

    def move_onto_screen(self, image):
        if self.loc[0] < 0:
            print("Moved bubble from off the left side of the image")
            self.loc = (0, self.loc[1])
        if self.loc[0] + self.width > image.size[0]:
            print("Moved bubble from off the right side of the image")
            self.loc = (image.size[0] - self.width, self.loc[1])
        if self.loc[1] < 0:
            print("Moved bubble from off the top of the image")
            self.loc = (self.loc[0], 0)
        if self.loc[1] + self.height > image.size[1]:
            print("Moved bubble from off the bottom of the image")
            self.loc = (self.loc[0], image.size[1] - self.height)

    def draw(self, image):
        """
        Draws a triangle, then an ellipse, then another triangle to remove part of the border, then the text
        :param image: PIL Image to draw on
        :return: The modified PIL Image
        """

        ARROW_WIDTH = 10

        draw = ImageDraw.Draw(image)
        # Define the location and size of the text bubble
        bubble_rect = [self.loc[0], self.loc[1], self.loc[0] + self.width, self.loc[1] + self.height]

        center_x = self.loc[0] + self.width / 2
        center_y = self.loc[1] + self.height / 2

        # Draw a triangle from the head edge to the text bubble
        head_edge_x = self.point_to_loc[0]
        head_edge_y = self.point_to_loc[1]

        # Calculate two offset points from the center of the ellipse perpendicular to the line to the point_to_loc
        angle = math.atan2(head_edge_y - (self.loc[1] + self.height / 2), head_edge_x - (self.loc[0] + self.width / 2))

        # p1 and p2 are near the center of the ellipse but, a couple of pixels perpendicular to the line to the point_to_loc
        p1 = (center_x + ARROW_WIDTH * math.cos(angle + math.pi / 2),
              center_y + ARROW_WIDTH * math.sin(angle + math.pi / 2))
        p2 = (center_x + ARROW_WIDTH * math.cos(angle - math.pi / 2),
              center_y + ARROW_WIDTH * math.sin(angle - math.pi / 2))
        p3 = (head_edge_x, head_edge_y)

        # Draw the triangle
        draw.polygon([p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]], fill='white', outline='black', width=5)

        # Draw the bubble
        draw.ellipse(bubble_rect, fill='white', outline='black', width=5)

        ss = 0.6

        # Draw a triangle to remove part of the border
        p1 = (center_x + ARROW_WIDTH * ss * math.cos(angle + math.pi / 2),
              center_y + ARROW_WIDTH * ss * math.sin(angle + math.pi / 2))
        p2 = (center_x + ARROW_WIDTH * ss * math.cos(angle - math.pi / 2),
              center_y + ARROW_WIDTH * ss * math.sin(angle - math.pi / 2))
        p3 = (head_edge_x, head_edge_y)

        # Draw the triangle
        draw.polygon([p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]], fill='white', outline='white')

        # Add the text to the bubble
        text_width, text_height = calculate_text_size(self.text, font)
        text_top_left = (self.loc[0] + (self.width - text_width) / 2, self.loc[1] + (self.height - text_height) / 2)

        draw.text(text_top_left, self.text, fill='black', font=font, align="center",encoding="utf-8")

        # Draw a dot at the center of the bubble and at the head edge
        # draw.ellipse([self.loc[0] + self.width / 2 - 2, self.loc[1] + self.height / 2 - 2,
        #               self.loc[0] + self.width / 2 + 2, self.loc[1] + self.height / 2 + 2], fill='blue')
        # draw.ellipse([head_edge_x - 2, head_edge_y - 2, head_edge_x + 2, head_edge_y + 2], fill='red')

        return image


def add_text_bubbles(image: Image, frame):
    """
    Adds text bubbles to an image
    :param image: PIL Image that the text bubbles will be added to
    :param character_moments: A list of CharacterMoments in the frame
    :return: A PIL Image with text bubbles
    """

    character_moments = frame.character_moments

    """
    Getting a bubble for each character in the frame
    """

    print(f"adding text bubbles to {len(character_moments)} characters)")

    text_bubbles = []
    already_used_locations = []
    for character_moment in character_moments:
        physical_description = character_moment.physical_description
        dialogue = character_moment.dialogue

        print("Adding text bubble for", physical_description, "with dialogue", dialogue)

        # Wrap the text
        dialogue = wrap_text(dialogue, 500)
        text_width, text_height = calculate_text_size(dialogue, font)

        bubble_width = text_width + font_size * 2
        bubble_height = text_height + font_size * 2

        vals = get_location(image, [physical_description], already_used_locations)
        head_location = (vals[0], vals[1])
        logits = vals[2]
        already_used_locations.append(head_location)

        head_edge = find_head_edge(image, head_location, logits)
        bubble_top_left = pick_relative_location(image, head_location, bubble_width, bubble_height)

        # Moving the bubble up or down from the head_edge if they have a similar y value
        if abs(bubble_top_left[1] - head_edge[1]) < 10:
            bubble_top_left = (bubble_top_left[0], head_edge[1] - bubble_height - 20)

        # Checking if the bubble is off the left or right side of the image
        if bubble_top_left[0] < 0:
            bubble_top_left = (0, bubble_top_left[1])
        if bubble_top_left[0] + bubble_width > image.size[0]:
            bubble_top_left = (image.size[0] - bubble_width, bubble_top_left[1])

        text_bubbles.append(
            TextBubble(bubble_top_left, bubble_width, bubble_height, head_edge, dialogue, head_location))

    """
        Moving bubbles onto the screen for the first time 
        This will induce other problems that can be fixed onwards
        """
    for text_bubble in text_bubbles:
        text_bubble.move_onto_screen(image)

    """
    Checking for bubbles covering the faces of other characters that have dialogue bubbles
    """
    for _ in range (2):
        all_face_locations = [text_bubble.point_to_loc for text_bubble in text_bubbles]
        for i, text_bubble in enumerate(text_bubbles):
            for j, face_location in enumerate(all_face_locations):
                if text_bubble.loc[0] < face_location[0] < text_bubble.loc[0] + text_bubble.width and \
                        text_bubble.loc[1] < face_location[1] < text_bubble.loc[1] + text_bubble.height:
                    # If the face is covered by a bubble, move the bubble down and towards the center
                    print("COVERING FACE")
                    direction = 1 if text_bubble.loc[0] < image.size[0] / 2 else -1
                    text_bubble.loc = (text_bubble.loc[0] + 80 * direction, face_location[1] + text_bubble.height + 80)



    """
    Deconflicting bubbles that may overlap or cross each other with their triangles
    """
    for i in range(len(text_bubbles)):
        for j in range(i + 1, len(text_bubbles)):
            if text_bubbles[i].loc[0] < text_bubbles[j].loc[0] + text_bubbles[j].width and \
                    text_bubbles[i].loc[0] + text_bubbles[i].width > text_bubbles[j].loc[0] and \
                    text_bubbles[i].loc[1] < text_bubbles[j].loc[1] + text_bubbles[j].height and \
                    text_bubbles[i].loc[1] + text_bubbles[i].height > text_bubbles[j].loc[1]:
                # If the bubbles overlap, move the second bubble down
                print("BUBBLES OVERLAPPING, MOVING ONE DOWN")
                text_bubbles[j].loc = (text_bubbles[j].loc[0], text_bubbles[i].loc[1] + text_bubbles[i].height)

    """
    Moving bubbles so they are entirely on the screen
    A second time to ensure that the bubbles are entirely on the screen
    It looks really bad if the bubbles are cut off
    """
    for text_bubble in text_bubbles:
        text_bubble.move_onto_screen(image)


    """
    Drawing the bubbles and triangles
    """

    for text_bubble in text_bubbles:
        image = text_bubble.draw(image)

    # Extending the image by 120 pixels at the bottom to put the scene description
    # Create a new blank image with the desired dimensions
    new_image = Image.new("RGB", (image.width, image.height + 120), color="white")

    # Paste the original image onto the new blank image
    new_image.paste(image, (0, 0))
    image = new_image
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, image.size[1] - 120, image.size[0], image.size[1]], fill='white')
    draw.text((10, image.size[1] - 110), wrap_text(frame.scene_description, 900), fill='black', font=font)

    return image


if __name__ == "__main__":
    # Example usage

    print("starting example usage of text_bubble.py")

    cat = CharacterMoment(Character("Iron Man",
                                         "red and gold suit",
                                         "at the left"), "At the left", "نحن بحاجة لإنقاذ حياة هذا الكلب.")
    boy = CharacterMoment(Character("Batman",
                                         "blue and black suit",
                                         "at the right"), "at the right", "أنت على حق. لنفعل ذلك.")
    #girl = CharacterMoment(Character("dog",
    #                                     "at the left",
    #                                     "at the left")," at the left", "Waiting for some food.")
    #rabbit = CharacterMoment(Character("rabbit",
    #                                     "blue rabbit.",
    #                                     "serious"), "serious at the right", "How long should we wait.")
    description = "العطف"
    frame = Frame(description,[cat, boy])
    output = add_text_bubbles(Image.open("interactivity/seq4.webp"), frame)
    # Save the image
    output.save("img_ar.jpg")
    # Show the image
    output.show()