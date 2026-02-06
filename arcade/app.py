from http.server import HTTPServer, BaseHTTPRequestHandler
import json, random

users = {}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        if 'status' in self.path:
            self.wfile.write(json.dumps({'status': 'running', 'games': ['slot', 'dice']}).encode())
        elif 'games' in self.path:
            self.wfile.write(json.dumps({'games': [
                {'id': 'slot', 'name': '🎰 Lucky Slot', 'min': 1, 'max': 100},
                {'id': 'dice', 'name': '🎲 Dice', 'min': 1, 'max': 100}
            ]}).encode())
        elif 'player' in self.path:
            uid = self.path.split('/')[-1]
            u = users.get(uid, {'balance': 1000, 'games': 0})
            self.wfile.write(json.dumps({'player_id': uid, 'balance': u['balance'], 'games_played': u.get('games', 0)}).encode())
        else:
            self.wfile.write(json.dumps({'error': 'not found'}).encode())
    
    def do_POST(self):
        try:
            d = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
        except:
            d = {}
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        uid = d.get('player_id', 'guest')
        if uid not in users:
            users[uid] = {'balance': 1000, 'games': 0}
        
        if 'play' in self.path:
            game = d.get('game')
            bet = d.get('bet', 10)
            
            if users[uid]['balance'] < bet:
                self.wfile.write(json.dumps({'error': 'Insufficient balance'}).encode())
                return
            
            users[uid]['balance'] -= bet
            users[uid]['games'] += 1
            
            if game == 'slot':
                s = [random.choice(['🍒','🍋','💎','7️⃣','🎰','💰']) for _ in range(3)]
                mult = {'💎💎💎':100,'7️⃣7️⃣7️⃣':50,'🎰🎰🎰':25,'💰💰💰':15,'🍒🍒🍒':5,'🍋🍋🍋':3}.get(''.join(s), 0)
                win = bet * mult
                users[uid]['balance'] += win
                self.wfile.write(json.dumps({
                    'game': 'slot', 'symbols': s, 'bet': bet, 
                    'winnings': win, 'balance': users[uid]['balance'],
                    'message': f'You won {win} MOLTY!' if win else 'Try again!'
                }).encode())
            
            elif game == 'dice':
                r = random.randint(1, 100)
                pred = d.get('prediction', 'high')
                won = (pred == 'high' and r > 50) or (pred == 'low' and r <= 50)
                win = bet * 2 if won else 0
                users[uid]['balance'] += win
                self.wfile.write(json.dumps({
                    'game': 'dice', 'roll': r, 'prediction': pred,
                    'bet': bet, 'winnings': win, 'balance': users[uid]['balance'],
                    'message': f'You won {win} MOLTY!' if won else 'You lost!'
                }).encode())
            else:
                users[uid]['balance'] += bet
                self.wfile.write(json.dumps({'error': 'Invalid game'}).encode())
        else:
            self.wfile.write(json.dumps({'error': 'Unknown endpoint'}).encode())

print("🎰 Starting MOLTY Arcade on port 8890...")
HTTPServer(('0.0.0.0', 8890), H).serve_forever()
