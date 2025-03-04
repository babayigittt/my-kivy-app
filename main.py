import os
import json
import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Triangle, Ellipse
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen

# --- BACKGROUND WIDGET ---
class BackgroundWidget(Widget):
    color = ListProperty([0.6, 1, 0.6, 1])
    def __init__(self, duration=10, safe_colors=None, **kwargs):
        super(BackgroundWidget, self).__init__(**kwargs)
        if safe_colors is None:
            safe_colors = [
                [0.2, 0.2, 0.2, 1],
                [0.3, 0.3, 0.3, 1],
                [0.4, 0.4, 0.4, 1]
            ]
        self.safe_colors = safe_colors
        with self.canvas:
            self.bg_color = Color(*self.color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect, color=self._update_color)
        self.current_index = 0
        self.animate_to_next(duration)
    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    def _update_color(self, instance, value):
        self.bg_color.rgba = value
    def animate_to_next(self, duration):
        next_index = (self.current_index + 1) % len(self.safe_colors)
        next_color = self.safe_colors[next_index]
        self.current_index = next_index
        anim = Animation(color=next_color, duration=duration)
        anim.bind(on_complete=lambda a, w: self.animate_to_next(duration))
        anim.start(self)

# --- CHARACTER PREVIEW ---
class CharacterPreview(Widget):
    def __init__(self, character_type, **kwargs):
        super(CharacterPreview, self).__init__(**kwargs)
        self.character_type = character_type
        self.size_hint = (None, None)
        self.size = (50, 50)
        self.pos = (0, 0)
        self.draw_preview()
    def draw_preview(self):
        self.canvas.clear()
        if self.character_type == 0:
            with self.canvas:
                Color(1, 0, 0)
                Rectangle(pos=self.pos, size=self.size)
        elif self.character_type in [1,2]:
            with self.canvas:
                if self.character_type == 1:
                    Color(1,1,1)
                else:
                    Color(1,0.75,0.8)
                Triangle(points=[self.x, self.y,
                                 self.x + self.width, self.y,
                                 self.x + self.width/2, self.y + self.height])
        elif self.character_type == 3:
            with self.canvas:
                Color(1,0,0)
                Ellipse(pos=self.pos, size=self.size)
                Color(1,1,0,0.5)
                Ellipse(pos=(self.x-5, self.y-5), size=(self.width+10, self.height+10))
    def on_pos(self, instance, value):
        self.draw_preview()
    def on_size(self, instance, value):
        self.draw_preview()

# --- PLAYER ---
class Player(Widget):
    velocity_y = NumericProperty(0)
    gravity = -0.5
    jump_velocity = 10
    def __init__(self, **kwargs):
        super(Player, self).__init__(**kwargs)
        self.app = App.get_running_app()
        # Seçili karakter App.selected_character_type'den alınır.
        self.character_type = self.app.selected_character_type  # 0: free red square, 1: white triangle, 2: pink triangle, 3: red circle
        if self.character_type == 3:
            self.lives = 2
        else:
            self.lives = 1
        self.size_hint = (None, None)
        self.size = (50, 50)
        self.pos = (100, 0)
        print(f"[DEBUG] Player __init__: character_type = {self.character_type}")
        self.draw_character()
        self.bind(pos=self.update_graphics, size=self.update_graphics)
    def draw_character(self):
        self.canvas.clear()
        if self.character_type == 0:
            print("[DEBUG] Drawing free red square")
            with self.canvas:
                Color(1, 0, 0)
                self.shape = Rectangle(pos=self.pos, size=self.size)
        elif self.character_type in [1, 2]:
            with self.canvas:
                if self.character_type == 1:
                    Color(1, 1, 1)
                else:
                    Color(1, 0.75, 0.8)
                self.shape = Triangle(points=[self.x, self.y,
                                              self.x + self.width, self.y,
                                              self.x + self.width/2, self.y + self.height])
        elif self.character_type == 3:
            with self.canvas:
                Color(1, 0, 0)
                self.shape = Ellipse(pos=self.pos, size=self.size)
                Color(1, 1, 0, 0.5)
                self.glow = Ellipse(pos=(self.x - 10, self.y - 10), size=(self.width + 20, self.height + 20))
    def update_graphics(self, *args):
        if self.character_type == 0:
            self.shape.pos = self.pos
            self.shape.size = self.size
        elif self.character_type in [1, 2]:
            self.shape.points = [self.x, self.y,
                                 self.x + self.width, self.y,
                                 self.x + self.width/2, self.y + self.height]
        elif self.character_type == 3:
            self.shape.pos = self.pos
            self.shape.size = self.size
            self.glow.pos = (self.x - 10, self.y - 10)
            self.glow.size = (self.width + 20, self.height + 20)
    def update(self):
        self.velocity_y += self.gravity
        new_y = self.y + self.velocity_y
        if new_y < 0:
            new_y = 0
            self.velocity_y = 0
        self.y = new_y
    def jump(self):
        if self.y == 0:
            self.velocity_y = self.jump_velocity

# --- OBSTACLE ---
class Obstacle(Widget):
    def __init__(self, **kwargs):
        super(Obstacle, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (40, 40)
        with self.canvas:
            Color(0, 0, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
    def update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    def update(self):
        multiplier = self.parent.speed_multiplier if self.parent and hasattr(self.parent, 'speed_multiplier') else 1
        self.x -= 5 * multiplier
        if self.x < -self.width:
            if self.parent:
                self.parent.remove_widget(self)

# --- COIN ---
class Coin(Widget):
    def __init__(self, **kwargs):
        super(Coin, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (30, 30)
        with self.canvas:
            Color(1, 1, 0)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
    def update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    def update(self):
        multiplier = self.parent.speed_multiplier if self.parent and hasattr(self.parent, 'speed_multiplier') else 1
        self.x -= 5 * multiplier
        if self.x < -self.width:
            if self.parent:
                self.parent.remove_widget(self)

# --- RUNNER GAME (oyun ekranı) ---
class RunnerGame(FloatLayout):
    score = NumericProperty(0)
    speed_multiplier = NumericProperty(1)
    elapsed_time = NumericProperty(0)
    def __init__(self, **kwargs):
        super(RunnerGame, self).__init__(**kwargs)
        self.size_hint = (1, 1)
        self.game_over = False
        self.elapsed_time = 0
        self.speed_multiplier = 1
        in_game_colors = [
            [0.5, 0.5, 0.5, 1],    # gri
            [0.0, 0.8, 0.0, 1],    # yeşil
            [1.0, 0.5, 0.0, 1],    # turuncu
            [0.5, 0.0, 0.5, 1],    # mor
            [0.6, 0.4, 0.2, 1],    # kahverengi
            [0.0, 0.0, 0.0, 1],    # siyah
            [0.0, 0.8, 0.8, 1]     # turkuaz
        ]
        self.bg = BackgroundWidget(duration=3, safe_colors=in_game_colors, size=self.size, pos=self.pos)
        self.add_widget(self.bg, index=0)
        self.player = Player()
        self.add_widget(self.player)
        self.total_coins_label = Label(text=f"Total Coins: {App.get_running_app().total_coins}",
                                       size_hint=(None, None), size=(200, 50),
                                       pos_hint={'x': 0, 'top': 1},
                                       disabled=True)
        self.add_widget(self.total_coins_label)
        self.score_label = Label(text=f"Score: {self.score}",
                                 size_hint=(None, None), size=(200, 50),
                                 pos_hint={'x': 0, 'top': 0.95},
                                 disabled=True)
        self.add_widget(self.score_label)
        self.bind(score=self.update_score_label)
        self.top_score_label = Label(text=f"Top Score: {App.get_running_app().top_score}",
                                     size_hint=(None, None), size=(200, 50),
                                     pos_hint={'x': 0, 'top': 0.90},
                                     disabled=True)
        self.add_widget(self.top_score_label)
        if self.player.character_type == 3:
            self.heart_label = Label(text=f"Lives: {self.player.lives}",
                                     size_hint=(None, None), size=(200, 50),
                                     pos_hint={'x': 0, 'top': 0.85},
                                     disabled=True)
            self.add_widget(self.heart_label)
        Clock.schedule_interval(self.update, 1.0/60.0)
        Clock.schedule_interval(self.spawn_objects, 2.0)
    def update_score_label(self, instance, value):
        self.score_label.text = f"Score: {value}"
        app = App.get_running_app()
        self.total_coins_label.text = f"Total Coins: {app.total_coins}"
        self.top_score_label.text = f"Top Score: {app.top_score}"
    def update(self, dt):
        if self.game_over:
            return True
        self.elapsed_time += dt
        if self.elapsed_time > 10:
            self.speed_multiplier = 1 + (self.elapsed_time - 10) * 0.1
        else:
            self.speed_multiplier = 1
        self.player.update()
        for child in self.children[:]:
            if isinstance(child, (Obstacle, Coin)):
                child.update()
                if self.player.collide_widget(child):
                    if isinstance(child, Coin):
                        self.score += 1
                        app = App.get_running_app()
                        app.total_coins += 1
                        if self.score > App.get_running_app().top_score:
                            App.get_running_app().top_score = self.score
                        print("Coin collected! Score:", self.score, "Total Coins:", app.total_coins)
                        self.remove_widget(child)
                    elif isinstance(child, Obstacle):
                        if self.player.character_type == 3 and self.player.lives > 1:
                            self.player.lives -= 1
                            if hasattr(self, 'heart_label'):
                                self.heart_label.text = f"Lives: {self.player.lives}"
                            self.remove_widget(child)
                            print("Hit! Lives left:", self.player.lives)
                        else:
                            print("Hit! Game Over. Final Score:", self.score)
                            self.game_over = True
                            Clock.unschedule(self.update)
                            Clock.unschedule(self.spawn_objects)
                            self.show_game_over_buttons()
        return True
    def spawn_objects(self, dt):
        obj_type = random.choice(['obstacle', 'coin'])
        if obj_type == 'obstacle':
            obj = Obstacle()
            obj.pos = (self.width, 0)
        else:
            obj = Coin()
            obj.pos = (self.width, random.randint(50, 100))
        self.add_widget(obj)
    def on_touch_down(self, touch):
        if not self.game_over:
            self.player.jump()
            return True
        return super(RunnerGame, self).on_touch_down(touch)
    def show_game_over_buttons(self):
        if hasattr(self, 'game_over_buttons_list'):
            return
        self.game_over_buttons_list = []
        play_again = Button(text="Play Again",
                            size_hint=(None, None), size=(200, 50),
                            pos_hint={'center_x': 0.5, 'center_y': 0.4},
                            background_normal='',
                            background_color=(0.2, 0.6, 0.8, 1))
        play_again.bind(on_release=self.reset_game)
        main_menu = Button(text="Main Menu",
                           size_hint=(None, None), size=(200, 50),
                           pos_hint={'center_x': 0.5, 'center_y': 0.3},
                           background_normal='',
                           background_color=(0.2, 0.6, 0.8, 1))
        main_menu.bind(on_release=self.go_to_menu)
        self.game_over_buttons_list.extend([play_again, main_menu])
        for btn in self.game_over_buttons_list:
            self.add_widget(btn)
    def reset_game(self, instance=None):
        if hasattr(self, 'game_over_buttons_list'):
            for btn in self.game_over_buttons_list:
                self.remove_widget(btn)
            del self.game_over_buttons_list
        self.game_over = False
        self.score = 0
        self.elapsed_time = 0
        self.speed_multiplier = 1
        self.player.character_type = App.get_running_app().selected_character_type
        self.player.draw_character()
        self.player.pos = (100, 0)
        self.player.velocity_y = 0
        for child in self.children[:]:
            if isinstance(child, (Obstacle, Coin)):
                self.remove_widget(child)
        Clock.unschedule(self.update)
        Clock.unschedule(self.spawn_objects)
        Clock.schedule_interval(self.update, 1.0/60.0)
        Clock.schedule_interval(self.spawn_objects, 2.0)
    def go_to_menu(self, instance):
        Clock.unschedule(self.update)
        Clock.unschedule(self.spawn_objects)
        App.get_running_app().root.current = 'menu'

# --- SCREENS ---
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MainMenuScreen, self).__init__(**kwargs)
        layout = FloatLayout()
        self.bg = BackgroundWidget(duration=10, size=Window.size, pos=(0, 0))
        layout.add_widget(self.bg, index=0)
        self.add_widget(layout)
        title = Label(text="Runner Game", font_size=32, bold=True,
                      size_hint=(None, None), size=(300, 50),
                      pos_hint={'center_x': 0.5, 'top': 1})
        layout.add_widget(title)
        play_button = Button(text="Play",
                             size_hint=(None, None), size=(220, 60),
                             pos_hint={'center_x': 0.5, 'center_y': 0.6},
                             background_normal='',
                             background_color=(0.2, 0.6, 0.8, 1),
                             font_size=20)
        play_button.bind(on_release=self.start_game)
        layout.add_widget(play_button)
        character_button = Button(text="Character",
                                  size_hint=(None, None), size=(220, 60),
                                  pos_hint={'center_x': 0.5, 'center_y': 0.5},
                                  background_normal='',
                                  background_color=(0.2, 0.6, 0.8, 1),
                                  font_size=20)
        character_button.bind(on_release=self.go_to_shop)
        layout.add_widget(character_button)
        self.total_coins_label = Label(text=f"Total Coins: {App.get_running_app().total_coins}",
                                         font_size=24, bold=True,
                                         size_hint=(None, None), size=(220, 50),
                                         pos_hint={'x': 0.05, 'top': 0.95})
        layout.add_widget(self.total_coins_label)
        self.top_score_label = Label(text=f"Top Score: {App.get_running_app().top_score}",
                                     font_size=24, bold=True,
                                     size_hint=(None, None), size=(220, 50),
                                     pos_hint={'x': 0.05, 'top': 0.90})
        layout.add_widget(self.top_score_label)
    def start_game(self, instance):
        self.manager.current = 'game'
    def go_to_shop(self, instance):
        self.manager.current = 'shop'
    def on_enter(self, *args):
        self.total_coins_label.text = f"Total Coins: {App.get_running_app().total_coins}"
        self.top_score_label.text = f"Top Score: {App.get_running_app().top_score}"

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.game_widget = RunnerGame()
        self.game_widget.size = Window.size
        self.game_widget.pos = (0, 0)
        self.add_widget(self.game_widget)
    def on_enter(self, *args):
        self.game_widget.reset_game()
    def on_leave(self, *args):
        pass

class CharacterShopScreen(Screen):
    def __init__(self, **kwargs):
        super(CharacterShopScreen, self).__init__(**kwargs)
        layout = FloatLayout()
        self.bg = BackgroundWidget(duration=10, size=Window.size, pos=(0, 0))
        layout.add_widget(self.bg, index=0)
        self.add_widget(layout)
        title = Label(text="Character Shop", font_size=32, bold=True,
                      size_hint=(None, None), size=(300, 50),
                      pos_hint={'center_x': 0.5, 'top': 1})
        layout.add_widget(title)
        self.base_texts = {
            0: "Free Red Square (Free)",
            1: "White Triangle (25)",
            2: "Pink Triangle (50)",
            3: "Red Circle (2 lives) (100)"
        }
        self.character_buttons = {}
        for char_type in range(4):
            y_pos = 0.8 - 0.1 * char_type
            btn = Button(text=self.base_texts[char_type],
                         size_hint=(None, None), size=(250, 60),
                         pos_hint={'center_x': 0.65, 'center_y': y_pos},
                         background_normal='',
                         background_color=(0.2, 0.6, 0.8, 1),
                         font_size=20)
            btn.bind(on_release=lambda x, ct=char_type: self.purchase_character(ct, 0 if ct==0 else (25 if ct==1 else (50 if ct==2 else 100))))
            self.character_buttons[char_type] = btn
            layout.add_widget(btn)
            preview = CharacterPreview(character_type=char_type, pos_hint={'center_x': 0.35, 'center_y': y_pos})
            layout.add_widget(preview)
        back_button = Button(text="Back",
                             size_hint=(None, None), size=(220, 60),
                             pos_hint={'center_x': 0.5, 'center_y': 0.3},
                             background_normal='',
                             background_color=(0.2, 0.6, 0.8, 1),
                             font_size=20)
        back_button.bind(on_release=self.go_back)
        layout.add_widget(back_button)
        self.message_label = Label(text="",
                                   font_size=24, bold=True,
                                   size_hint=(None, None), size=(300, 50),
                                   pos_hint={'center_x': 0.5, 'center_y': 0.2})
        layout.add_widget(self.message_label)
        self.update_tick_labels()
    def update_tick_labels(self):
        app = App.get_running_app()
        for char_type, btn in self.character_buttons.items():
            base = self.base_texts[char_type]
            if char_type == app.selected_character_type:
                btn.text = base + " ✔"
            else:
                btn.text = base
    def purchase_character(self, char_type, cost):
        app = App.get_running_app()
        if char_type in app.unlocked_characters:
            app.selected_character_type = char_type
            self.message_label.text = f"Character {char_type} selected!"
            self.update_tick_labels()
            app.save_progress()
        else:
            if cost == 0 or app.total_coins >= cost:
                if cost != 0:
                    app.total_coins -= cost
                app.unlocked_characters.append(char_type)
                app.selected_character_type = char_type
                self.message_label.text = f"Character {char_type} purchased and selected!"
                self.update_tick_labels()
                app.save_progress()
            else:
                self.message_label.text = "Not enough coins!"
    def go_back(self, instance):
        self.manager.current = 'menu'

class RunnerScreenManager(ScreenManager):
    pass

# --- APP ---
class RunnerApp(App):
    total_coins = NumericProperty(0)
    selected_character_type = NumericProperty(0)  # Default: 0 (free red square)
    top_score = NumericProperty(0)
    def build(self):
        # Eğer progress yüklenmişse, unlocked_characters korunmalı, aksi halde tanımla.
        if not hasattr(self, 'unlocked_characters'):
            self.unlocked_characters = [0]  # Ücretsiz karakter her zaman açık
        sm = RunnerScreenManager()
        sm.add_widget(MainMenuScreen(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(CharacterShopScreen(name='shop'))
        return sm
    def on_stop(self):
        data = {
            'total_coins': self.total_coins,
            'selected_character_type': self.selected_character_type,
            'unlocked_characters': self.unlocked_characters,
            'top_score': self.top_score
        }
        progress_path = os.path.join(self.user_data_dir, "progress.json")
        with open(progress_path, "w") as f:
            json.dump(data, f)
    def load_progress(self):
        progress_path = os.path.join(self.user_data_dir, "progress.json")
        if os.path.exists(progress_path):
            with open(progress_path, "r") as f:
                data = json.load(f)
                self.total_coins = data.get("total_coins", 0)
                self.selected_character_type = data.get("selected_character_type", 0)
                self.unlocked_characters = data.get("unlocked_characters", [0])
                self.top_score = data.get("top_score", 0)
    def save_progress(self):
        data = {
            'total_coins': self.total_coins,
            'selected_character_type': self.selected_character_type,
            'unlocked_characters': self.unlocked_characters,
            'top_score': self.top_score
        }
        progress_path = os.path.join(self.user_data_dir, "progress.json")
        with open(progress_path, "w") as f:
            json.dump(data, f)

if __name__ == '__main__':
    app = RunnerApp()
    app.load_progress()
    app.run()
