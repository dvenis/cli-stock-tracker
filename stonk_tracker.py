import pandas as pd
import yfinance as yf

import curses
from curses import wrapper

class Symbol:
  def __init__(self, name):
    self.name = name
    self.price = -1
    #self._open = -1
    self.previous_close = -1
  
  #@property
  #def name(self):
  #  return self._name

  @property 
  def percent_change(self):
    return (self.price / self.previous_close - 1) * 100
  
  #@property
  #def price(self):
  #  return self._price

  #@price.setter
  #def price(self, val):
  #  self._price = val
  
  #@property
  #def open(self):
  #  return self._open
  
  #@open.setter
  #def open(self, val):
  #  self._open = val
  
def get_symbol(ticker):
  symbol = Symbol(ticker)
  try:
    yft_info = yf.Ticker(ticker).info
    symbol.price = (yft_info['bid'] + yft_info['ask'])/2
    symbol.previous_close = yft_info['regularMarketPreviousClose']
  except Exception:
    print('failed to get {}'.format(ticker))
  return symbol

def draw_symbol(stdscr, row, symbol):
  stdscr.addstr(row, 0, symbol.name)
  stdscr.addstr(row, 10, '{:.2f}'.format(symbol.price))

  if symbol.percent_change > 0:
    percent_color = curses.color_pair(1)
  elif symbol.percent_change < 0:
    percent_color = curses.color_pair(2)
  else:
    percent_color = curses.color_pair(0)
  stdscr.addstr(row, 20, '{:.2f}%'.format(symbol.percent_change), percent_color)

def draw_symbols(stdscr, symbols):
  for i, symbol in enumerate(symbols):
    draw_symbol(stdscr, i, symbol)

def follow_handler(stdscr, command, args):
  stdscr.addstr(6, 0, 'following!')
  symbols.append(get_symbol(args[0]))
  draw_symbols(stdscr, symbols)

def unfollow_handler(stdscr, command, args):
  stdscr.addstr(6, 0, 'unfollowing...')

def exit_handler(stdscr, command, args):
  exit()

def unknown_command_handler(stdscr, command, args):
  stdscr.addstr(6, 0, 'unknown command')

UNKNOWN_COMMAND = ''

command_handlers = {
  'follow': follow_handler,
  'unfollow': unfollow_handler,
  'exit': exit_handler,
  '': unknown_command_handler,
}

schd = Symbol('SCHD')
schd.price = 50.1
schd.previous_close = 52

ivv = Symbol('IVV')
ivv.price = 201.5
ivv.previous_close = 190

spy = Symbol('SPY')
spy.price = 291.5
spy.previous_close = 291.5

symbols = []#[schd, ivv, spy]

def main(stdscr):
  stdscr.clear()

  curses.use_default_colors()
  curses.init_pair(1, curses.COLOR_GREEN, -1)
  curses.init_pair(2, curses.COLOR_RED, -1)

  for row, symbol in enumerate(symbols):
    draw_symbol(stdscr, row, symbol)

  while True:
    key = stdscr.getkey()
    if key == ':':
      # commands
      stdscr.addstr(5, 0, key)
      curses.echo()
      command_input = stdscr.getstr(5, 1, 128).decode('utf-8')
      curses.noecho()

      command_input = command_input.split(' ')
      command = UNKNOWN_COMMAND
      args = []

      if len(command_input) > 0:
        command = command_input[0]
      if command not in command_handlers:
        command = UNKNOWN_COMMAND
      if len(command_input) > 1:
        args = command_input[1:]

      command_handlers[command](stdscr, command, args)

  stdscr.refresh()
  stdscr.getkey()

wrapper(main)
