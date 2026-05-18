import tkinter as tk
from tkinter import messagebox
import random
import time
import os

class KohsWithScores:
    def __init__(self, root):
        self.root = root
        self.root.title("Kohs-kocka Teszt + Eredménytábla")
        self.root.resizable(False, False)
        
        self.score_file = "kohs_scores.txt"
        
        # A 3 valós fizikai oldaltípus definíciója
        self.cube_faces = [
            {"type": "solid", "color": "red"},     # 0-s index: Tiszta piros
            {"type": "solid", "color": "white"},   # 1-es index: Tiszta fehér
            {"type": "diagonal", "c1": "red", "c2": "white"} # 2-es index: Átlós
        ]
        
        self.grid_size = 2          
        self.block_visual_size = 90  
        
        self.target_pattern = []
        self.player_pattern = []
        
        self.start_time = None
        self.timer_running = False
        self.timer_after_id = None
        
        self.high_scores = self.load_scores()
        
        self.create_widgets()
        self.generate_new_game()
        
    def create_widgets(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, pady=10, padx=20)
        
        title = tk.Label(top_frame, text="Kohs-kocka (Block Design) Teszt", font=("Arial", 16, "bold"))
        title.pack(side=tk.LEFT)
        
        level_frame = tk.Frame(top_frame)
        level_frame.pack(side=tk.RIGHT)
        
        tk.Label(level_frame, text="Méret:", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5)
        
        for size in [2, 3, 4]:
            btn = tk.Button(level_frame, text=f"{size}x{size}", font=("Arial", 10, "bold"), 
                            command=lambda s=size: self.change_difficulty(s), width=5, bg="#e0e0e0")
            btn.pack(side=tk.LEFT, padx=2)
            
        self.timer_label = tk.Label(self.root, text="Idő: 0.0 mp", font=("Arial", 14, "bold"), fg="#222")
        self.timer_label.pack(pady=5)
        
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=20, pady=10)
        
        self.target_frame = tk.LabelFrame(self.main_frame, text=" Tesztkártya ", font=("Arial", 11, "bold"), fg="darkblue")
        self.target_frame.pack(side=tk.LEFT, padx=10)
        
        self.target_canvas = tk.Canvas(self.target_frame, bg="#eee")
        self.target_canvas.pack(pady=5)
        
        self.player_frame = tk.LabelFrame(self.main_frame, text=" Kockáid (Kattints rájuk!) ", font=("Arial", 11, "bold"), fg="darkgreen")
        self.player_frame.pack(side=tk.LEFT, padx=10)
        
        self.player_canvas = tk.Canvas(self.player_frame, bg="#eee")
        self.player_canvas.pack(pady=5)
        self.player_canvas.bind("<Button-1>", self.on_canvas_click)
        
        self.score_frame = tk.LabelFrame(self.main_frame, text="Egyéni Rekordok ", font=("Arial", 11, "bold"), fg="#b8860b")
        self.score_frame.pack(side=tk.LEFT, padx=15, fill=tk.Y)
        
        self.score_labels = {}
        for size in [2, 3, 4]:
            lbl = tk.Label(self.score_frame, text="", font=("Arial", 10, "bold"), anchor="w", justify=tk.LEFT, pady=8, padx=10)
            lbl.pack(fill=tk.X)
            self.score_labels[size] = lbl
        self.update_score_display()
        
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(fill=tk.X, pady=15, padx=20)
        
        self.check_button = tk.Button(self.control_frame, text="Kész vagyok (Ellenőrzés)", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=self.check_result)
        self.check_button.pack(side=tk.LEFT, padx=10)
        
        self.next_button = tk.Button(self.control_frame, text="Új kártya", font=("Arial", 11), bg="#2196F3", fg="white", command=self.generate_new_game)
        self.next_button.pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(self.control_frame, text="A mérés elindult!", font=("Arial", 11, "italic"), fg="#555")
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def change_difficulty(self, new_size):
        self.grid_size = new_size
        self.generate_new_game()

    def draw_block(self, canvas, row, col, block_state):
        s = self.block_visual_size
        x1, y1 = col * s, row * s
        x2, y2 = x1 + s, y1 + s
        
        face = self.cube_faces[block_state["face_idx"]]
        rot = block_state["rotation"]
        
        if face["type"] == "solid":
            canvas.create_rectangle(x1, y1, x2, y2, fill=face["color"], outline="#222", width=2)
        elif face["type"] == "diagonal":
            if rot == 0:
                p1, p2 = [0,0, 1,0, 0,1], [1,1, 1,0, 0,1]
            elif rot == 1:
                p1, p2 = [0,0, 1,0, 1,1], [0,0, 0,1, 1,1]
            elif rot == 2:
                p1, p2 = [1,0, 1,1, 0,1], [1,0, 0,0, 0,1]
            elif rot == 3:
                p1, p2 = [0,0, 0,1, 1,1], [0,0, 1,0, 1,1]
                
            pts1 = [x1 + x*s for x in p1]
            pts2 = [x1 + x*s for x in p2]
            
            canvas.create_polygon(pts1, fill=face["c1"], outline="#222", width=2)
            canvas.create_polygon(pts2, fill=face["c2"], outline="#222", width=2)

    def generate_new_game(self):
        if self.timer_after_id:
            self.root.after_cancel(self.timer_after_id)
            self.timer_after_id = None
            
        self.timer_running = False
        
        canvas_res = self.grid_size * self.block_visual_size
        
        self.target_canvas.config(width=canvas_res, height=canvas_res, highlightthickness=0, bd=0)
        self.player_canvas.config(width=canvas_res, height=canvas_res, highlightthickness=0, bd=0)
        
        # JAVÍTÁS: Célminta tiszta, egymásba ágyazott listagenerátorral (Minden cella garantáltan egyedi objektum)
        self.target_pattern = [
            [{"face_idx": random.randint(0, 2), "rotation": random.randint(0, 3)} for _ in range(self.grid_size)] 
            for _ in range(self.grid_size)
        ]
        
        # JAVÍTÁS: Játékos rácsa tiszta, egymásba ágyazott listagenerátorral (Nincs mutató-összeakadás, nincs szomszéd-forgatás)
        self.player_pattern = [
            [{"face_idx": 1, "rotation": 0} for _ in range(self.grid_size)] 
            for _ in range(self.grid_size)
        ]
        
        self.render_all()
        self.root.update_idletasks()
        
        self.start_time = time.time()
        self.timer_running = True
        self.update_timer()
        self.status_label.config(text="Idő mérése folyamatban...", fg="black", font=("Arial", 11, "italic"))
    
    def update_timer(self):
        if self.timer_running and self.start_time:
            elapsed = time.time() - self.start_time
            self.timer_label.config(text=f"Idő: {elapsed:.1f} mp")
            self.timer_after_id = self.root.after(100, self.update_timer)

    def render_all(self):
        self.target_canvas.delete("all")
        self.player_canvas.delete("all")
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                self.draw_block(self.target_canvas, r, c, self.target_pattern[r][c])
                self.draw_block(self.player_canvas, r, c, self.player_pattern[r][c])

    def on_canvas_click(self, event):
        col = int(event.x / self.block_visual_size)
        row = int(event.y / self.block_visual_size)
        
        if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
            current = self.player_pattern[row][col]
            
            # Valódi forgatási logika
            if self.cube_faces[current["face_idx"]]["type"] == "diagonal":
                if current["rotation"] < 3:
                    current["rotation"] += 1
                else:
                    current["rotation"] = 0
                    current["face_idx"] = (current["face_idx"] + 1) % 3
            else:
                current["face_idx"] = (current["face_idx"] + 1) % 3
                current["rotation"] = 0
                
            self.render_all()

    def check_result(self):
        match = True
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                p_cell = self.player_pattern[r][c]
                t_cell = self.target_pattern[r][c]
                
                if p_cell["face_idx"] != t_cell["face_idx"]:
                    match = False
                    break
                
                # Ha átlós szín, a rotációnak (szögnek) is egyeznie kell
                if t_cell["face_idx"] == 2:
                    if p_cell["rotation"] != t_cell["rotation"]:
                        match = False
                        break
            if not match:
                break
                        
        if match:
            if self.timer_running:
                self.timer_running = False
                if self.timer_after_id:
                    self.root.after_cancel(self.timer_after_id)
                    self.timer_after_id = None
                    
            elapsed = round(time.time() - self.start_time, 1)
            is_new_record = False
            old_score = self.high_scores.get(self.grid_size)
            
            if old_score is None or elapsed < old_score:
                self.high_scores[self.grid_size] = elapsed
                self.save_scores()
                self.update_score_display()
                is_new_record = True
            
            if is_new_record:
                self.status_label.config(text=f"ÚJ REKORD! {elapsed} mp!", fg="green", font=("Arial", 11, "bold"))
                messagebox.showinfo("Gratulálunk!", f"Új egyéni csúcs a(z) {self.grid_size}x{self.grid_size} rácson:\n{elapsed} másodperc!")
            else:
                self.status_label.config(text=f"SIKER! Kirakva: {elapsed} mp alatt.", fg="green", font=("Arial", 11, "bold"))
        else:
            self.status_label.config(text="Nem egyezik a minta! Keresd a hibát!", fg="red", font=("Arial", 11, "bold"))

    def load_scores(self):
        scores = {2: None, 3: None, 4: None}
        if os.path.exists(self.score_file):
            try:
                with open(self.score_file, "r") as f:
                    for line in f:
                        if line.strip():
                            size, score = line.strip().split(":")
                            scores[int(size)] = float(score)
            except Exception:
                pass 
        return scores

    def save_scores(self):
        try:
            with open(self.score_file, "w") as f:
                for size, score in self.high_scores.items():
                    if score is not None:
                        f.write(f"{size}:{score}\n")
        except Exception as e:
            print(f"Hiba a mentés során: {e}")

    def update_score_display(self):
        for size, label in self.score_labels.items():
            score = self.high_scores[size]
            if score is not None:
                label.config(text=f"• {size}x{size} rács:\n  {score} mp", fg="#222")
            else:
                label.config(text=f"• {size}x{size} rács:\n  -- mp", fg="#777")

if __name__ == "__main__":
    root = tk.Tk()
    app = KohsWithScores(root)
    root.mainloop()