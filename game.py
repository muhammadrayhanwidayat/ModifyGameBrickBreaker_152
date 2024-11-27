# Import library tkinter untuk membuat GUI
import tkinter as tk

# Kelas dasar untuk semua objek permainan (bola, paddle, bricks)
class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas  # Objek canvas tempat item digambar
        self.item = item      # Representasi grafis dari objek di canvas

    def get_position(self):
        # Mengembalikan posisi objek (x1, y1, x2, y2)
        return self.canvas.coords(self.item)

    def move(self, x, y):
        # Memindahkan objek di canvas berdasarkan offset x dan y
        self.canvas.move(self.item, x, y)

    def delete(self):
        # Menghapus objek dari canvas
        self.canvas.delete(self.item)


# Kelas bola yang dapat bergerak dan memantul di canvas
class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10              # Radius bola
        self.direction = [1, -1]      # Arah bola (x, y)
        self.speed = 5                # Kecepatan awal bola
        # Membuat objek bola berbentuk lingkaran
        item = canvas.create_oval(x - self.radius, y - self.radius, 
                                  x + self.radius, y + self.radius, 
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        # Memperbarui posisi bola berdasarkan arah dan kecepatan
        coords = self.get_position()
        width = self.canvas.winfo_width()

        # Membalik arah bola jika menyentuh sisi kiri/kanan atau atas
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1

        # Menghitung pergerakan bola
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        # Mengatur respons bola saat bertabrakan dengan objek lain
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


# Kelas paddle (platform yang dikontrol pemain)
class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80      # Lebar paddle
        self.height = 10     # Tinggi paddle
        self.ball = None     # Bola yang terhubung ke paddle (jika ada)
        # Membuat paddle berbentuk persegi panjang
        item = canvas.create_rectangle(x - self.width / 2, y - self.height / 2,
                                       x + self.width / 2, y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        # Menghubungkan bola ke paddle
        self.ball = ball

    def move(self, offset):
        # Menggerakkan paddle ke kiri atau kanan
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                # Menggerakkan bola bersama paddle (jika terhubung)
                self.ball.move(offset, 0)


# Kelas untuk balok yang harus dihancurkan
class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}  # Warna berdasarkan jumlah hit

    def __init__(self, canvas, x, y, hits):
        self.width = 75         # Lebar balok
        self.height = 20        # Tinggi balok
        self.hits = hits        # Jumlah hit yang diperlukan untuk menghancurkan balok
        # Membuat balok berbentuk persegi panjang
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2, y - self.height / 2,
                                       x + self.width / 2, y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        # Mengurangi kekuatan balok saat terkena bola
        self.hits -= 1
        if self.hits == 0:
            self.delete()  # Menghapus balok jika kekuatan habis
        else:
            # Mengubah warna balok berdasarkan kekuatan tersisa
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])


# Kelas utama untuk mengelola permainan
class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3           # Nyawa pemain
        self.width = 610         # Lebar canvas
        self.height = 400        # Tinggi canvas
        self.canvas = tk.Canvas(self, bg='#D6D1F5',
                                width=self.width, height=self.height)
        self.canvas.pack()
        self.pack()

        # Membuat latar belakang bergaris
        for i in range(0, self.height, 20):
            color = "#EFEFEF" if i // 20 % 2 == 0 else "#D6D1F5"
            self.canvas.create_rectangle(0, i, self.width, i + 20, fill=color, outline="")

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle

        # Menambahkan bricks dengan posisi dan kekuatan yang berbeda
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-10))  # Kontrol paddle kiri
        self.canvas.bind('<Right>', lambda _: self.paddle.move(10)) # Kontrol paddle kanan
        self.start_time = None
        self.speed_boost_alerted = False

    def setup_game(self):
        # Mengatur ulang permainan dengan bola baru dan teks awal
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200, 'Press Space to start')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        # Menambahkan bola ke permainan
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        # Menambahkan balok ke permainan
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):
        # Menampilkan teks di tengah canvas
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text, font=font)

    def update_lives_text(self):
        # Memperbarui teks nyawa pemain
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        # Memulai permainan dan loop utama
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.start_time = self.canvas.after(10000, self.increase_ball_speed)
        self.game_loop()

    def increase_ball_speed(self, elapsed_time=0):
        # Menambahkan kecepatan bola secara bertahap
        self.ball.speed += 2
        self.speed_boost_alerted = True
        alert_text = self.canvas.create_text(
            self.width / 2, self.height / 2,
            text="Kecepatan bola meningkat!",
            font=("Forte", 20),
            fill="red"
        )
        self.canvas.after(2000, lambda: self.canvas.delete(alert_text))
        self.start_time = self.canvas.after(10000, self.increase_ball_speed)

    def game_loop(self):
        # Loop utama permainan
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.draw_text(300, 200, 'You win!')
        elif self.ball.get_position()[3] >= self.height:
            self.lives -= 1
            if self.lives == 0:
                self.draw_text(300, 200, 'Game over!')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        # Memeriksa tabrakan antara bola dengan paddle atau bricks
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items.get(x) for x in items if x in self.items]
        self.ball.collide(objects)


# Blok untuk menjalankan permainan
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root)
    game.mainloop()
