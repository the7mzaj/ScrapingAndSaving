from manim import *

class BasicManimScene(Scene):
    def construct(self):
        # Create a square
        square = Square(color=BLUE, fill_opacity=0.5)
        circle = Circle(color=RED, fill_opacity=1)
        
        # Display the square
        self.play(Create(circle))
        self.play(Create(square))
        self.wait(1)
        
        # Move the square to the right
        self.play(square.animate.shift(RIGHT * 2))
        self.play(circle.animate.shift(LEFT*1.5))
        self.wait(1)
        
        # Rotate the square
        self.play(Rotate(square, angle=PI/4))
        self.wait(1)
        
        # Fade out the square
        self.play(FadeOut(square))
