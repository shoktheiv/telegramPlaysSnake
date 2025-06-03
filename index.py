import random
import time
import threading
import telebot
from telebot import types
from collections import defaultdict

# Configuration
TOKEN = 'nice try' 
CHANNEL_ID = -1002565479044 


bot = telebot.TeleBot(TOKEN)

class ChannelSnakeGame:
    def __init__(self):
        self.width = 8
        self.height = 7
        self.snake = [(self.width//2, self.height//2)]
        self.food = self.new_food()
        self.direction = (1, 0)
        self.score = 0
        self.game_over = False
        self.message_id = None
        self.votes = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        self.voters = defaultdict(str)  
        self.last_update = time.time()
        self.timer = None
        self.active = False
        self.message_history = []
    
    def new_food(self):
        while True:
            food = (random.randint(0, self.width-1), random.randint(0, self.height-1))
            if food not in self.snake:
                return food
    
    def update(self, direction=None):
        if direction:
            self.direction = direction
        
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % self.width, (head_y + dy) % self.height)
        
        if new_head in self.snake:
            self.game_over = True
            return False
        
        self.snake.insert(0, new_head)
        
        if new_head == self.food:
            self.score += 1
            self.food = self.new_food()
            return True
        else:
            self.snake.pop()
            return True
    
    def get_board(self):
        board = []
        board.append('⏺️' + '↔️' * self.width + '⏺️')
        for y in range(self.height):
            row = ['↕️']
            for x in range(self.width):
                if (x, y) == self.snake[0]:
                    row.append('🥵')
                elif (x, y) in self.snake:
                    row.append('🟠')
                elif (x, y) == self.food:
                    row.append('🍎')
                else:
                    row.append('⬜️')
            row.append('↕️')
            board.append(''.join(row))
        

        board.append('⏺️' + '↔️' * self.width + '⏺️')
        return '\n'.join(board)
    
    def get_keyboard(self):
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton(f'⬆️ Up ({self.votes["up"]})', callback_data='up'),
            types.InlineKeyboardButton(f'⬇️ Down ({self.votes["down"]})', callback_data='down')
        )
        markup.row(
            types.InlineKeyboardButton(f'⬅️ Left ({self.votes["left"]})', callback_data='left'),
            types.InlineKeyboardButton(f'➡️ Right ({self.votes["right"]})', callback_data='right')
        )
        return markup
    
    def get_status(self):
        time_left = int(300 - (time.time() - self.last_update))
        mins, secs = divmod(time_left, 60)
        return f"\n*💰Score:* {self.score} \n*⏰Next move in:* {mins:02d}:{secs:02d}"
    
    def send_update(self):
        if not self.active:
            return
        
        text = f"👅 *TELEGRAM PLAYS SNAKE* 👅\n{self.get_status()}\n\n{self.get_board()}\n\nVote For The Next Move:\n⏳"
        
        if self.game_over:
            text = f"🎮 *Game Over! 🎮\n💰Final Score:* {self.score}\n\n{self.get_board()} \n\n *🚨 NEW GAME IN 10 SECONDS 🚨*"
            try:
                msg = bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text,
                    parse_mode="Markdown"
                )
                self.message_history.append(msg.message_id)
            except Exception as e:
                print(f"Error sending message: {e}")
            self.active = False
            self.game_over_init()
            return
        
        try:
            msg = bot.send_message(
                chat_id=CHANNEL_ID,
                text=text,
                reply_markup=self.get_keyboard(),
                parse_mode='Markdown'
            )
            self.message_id = msg.message_id
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def update_votes(self):

        text = f"👅 *TELEGRAM PLAYS SNAKE* 👅\n{self.get_status()}\n\n{self.get_board()}\n\nVote For The Next Move:\n⏳"

        try:
            if self.message_id:
                bot.edit_message_text(
                    chat_id=CHANNEL_ID,
                    message_id=self.message_id,
                    text=text,
                    reply_markup=self.get_keyboard(),
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def game_over_init(self):
        self.timer = threading.Timer(10, handle_start)
        self.timer.start()

    def schedule_update(self):
        if not self.active:
            return
        
        self.timer = threading.Timer(300.0, self.execute_move)
        self.timer.start()
    
    def execute_move(self):
        if not self.active or self.game_over:
            return
        
        # Determine most voted direction
        max_votes = max(self.votes.values())
        if max_votes == 0:  # No votes, continue current direction
            chosen_direction = self.direction
        else:
            directions = [d for d, votes in self.votes.items() if votes == max_votes]
            direction_map = {
                'up': (0, -1),
                'down': (0, 1),
                'left': (-1, 0),
                'right': (1, 0)
            }
            chosen_direction = direction_map[directions[0]]
        
        # Update game state
        self.update(chosen_direction)
        self.last_update = time.time()
        self.votes = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        self.voters = defaultdict(str)
        
        # Send update and schedule next move
        self.send_update()
        if not self.game_over:
            self.schedule_update()

# Global game instance
game = ChannelSnakeGame()

@bot.channel_post_handler(commands=['start'])
def handle_start(message = None):

    if message != None:
        if message.chat.id != CHANNEL_ID:
            return
    
    if game.active:
        bot.reply_to(message, "⚠️ Game is already running!")
        return
    
    # Reset game state
    game.__init__()
    game.active = True
    game.game_over = False
    
    # Create initial message
    text = f"👅 *TELEGRAM PLAYS SNAKE* 👅\n{game.get_status()}\n\n{game.get_board()}\n\nVote For The Next Move:\n⏳"
    msg = bot.send_message(CHANNEL_ID, text=text, reply_markup=game.get_keyboard(), parse_mode="Markdown")
    game.message_id = msg.message_id
    game.message_history.append(msg.message_id)
    
    # Start the update cycle
    game.schedule_update()

@bot.callback_query_handler(func=lambda call: True)
def handle_vote(call):
    if call.message.chat.id != CHANNEL_ID:
        return
    
    if not game.active or game.game_over:
        bot.answer_callback_query(call.id, "Game not active. Start with /start")
        return
    
    user_id = call.from_user.id
    direction = call.data
    
    # Check if user already voted
    if user_id in game.voters:
        if game.voters[user_id] == direction:
            bot.answer_callback_query(call.id, "You already voted this direction!")
        else:
            # Remove previous vote
            prev_vote = game.voters[user_id]
            game.votes[prev_vote] -= 1
            # Add new vote
            game.votes[direction] += 1
            game.voters[user_id] = direction
            bot.answer_callback_query(call.id, f"Changed vote to {direction}!")
            game.update_votes()
    else:
        # New vote
        game.votes[direction] += 1
        game.voters[user_id] = direction
        bot.answer_callback_query(call.id, f"Voted {direction}!")
        game.update_votes()

@bot.channel_post_handler(commands=['stop'])
def handle_stop(message):
    if message.chat.id != CHANNEL_ID:
        return
    
    if not game.active:
        bot.reply_to(message, "⚠️ No active game to stop!")
        return
    
    game.active = False
    if game.timer:
        game.timer.cancel()
    bot.reply_to(message, "🐍 Game stopped!")

if __name__ == '__main__':
    print("Channel Snake Bot is running...")
    bot.infinity_polling()
