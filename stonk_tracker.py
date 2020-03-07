from enum import Enum

import pandas as pd
import yfinance as yf

import curses
from curses import wrapper

class Symbol:
  def __init__(self, name):
    self.name = name
    self.price = -1
    self.previous_close = -1
  
  @property 
  def percent_change(self):
    return (self.price / self.previous_close - 1) * 100

class OptionType(Enum):
  CALL = 1
  PUT = 2

def val(pd_object):
  return pd_object.values[0]
  
def get_stock(ticker):
  symbol = None
  try:
    yft_info = yf.Ticker(ticker).info
    symbol = Symbol(yft_info['symbol'])
    symbol.price = (yft_info['bid'] + yft_info['ask'])/2
    symbol.previous_close = yft_info['regularMarketPreviousClose']
  except Exception:
    print('failed to get {}'.format(ticker))
  return symbol



def get_option(ticker, date, strike, option_type):
  symbol = None
  try:
    yft_option_chain = yf.Ticker(ticker).option_chain(date)
    if option_type == OptionType.CALL:
      yft_options = yft_option_chain.calls
    elif option_type == OptionType.PUT:
      yft_options = yft_option_chain.puts
    yft_option = yft_options[yft_options['strike'] == strike]

    symbol = Symbol(val(yft_option['contractSymbol']))
    symbol.price = val((yft_option['bid'] + yft_option['ask'])/2)
    symbol.previous_close = 5 # TODO change symbol or something
  except Exception:
    print('failed to get {}'.format(ticker))
  return symbol

def draw_symbol(stdscr, row, symbol):
  stdscr.clrtoeol()
  stdscr.addstr(row, 0, symbol.name)
  stdscr.addstr(row, 20, '{:.2f}'.format(symbol.price))

  if symbol.percent_change > 0:
    percent_color = curses.color_pair(1)
  elif symbol.percent_change < 0:
    percent_color = curses.color_pair(2)
  else:
    percent_color = curses.color_pair(0)
  stdscr.addstr(row, 30, '{:.2f}%'.format(symbol.percent_change), percent_color)

def draw_symbols(stdscr, symbols):
  for i, symbol in enumerate(symbols):
    draw_symbol(stdscr, i, symbol)
  stdscr.refresh()

################################################################################
# Command Handlers
################################################################################

def follow_handler(stdscr, command, args):
  stdscr.addstr(6, 0, 'following!')
  symbol = get_stock(args[0])
  if symbol is not None:
    symbols.append(symbol)
    draw_symbols(stdscr, symbols)

def unfollow_handler(stdscr, command, args):
  stdscr.addstr(6, 0, 'unfollowing...')

def follow_call_handler(stdscr, command, args):
  # followoption SPY 2020-03-08
  symbol = get_option(args[0], args[1], float(args[2]), OptionType.CALL)
  if symbol is not None:
    symbols.append(symbol)
    draw_symbols(stdscr, symbols)

def follow_put_handler(stdscr, command, args):
  # followoption SPY 2020-03-08
  symbol = get_option(args[0], args[1], float(args[2]), OptionType.PUT)
  if symbol is not None:
    symbols.append(symbol)
    draw_symbols(stdscr, symbols)

def exit_handler(stdscr, command, args):
  exit()

def unknown_command_handler(stdscr, command, args):
  stdscr.addstr(6, 0, 'unknown command')

def read_command(stdscr):
  max_row, _ = stdscr.getmaxyx()
  stdscr.clrtoeol()
  # Draw at the bottom
  stdscr.addstr(max_row-1, 0, ':')
  curses.echo()
  command_input = stdscr.getstr(max_row-1, 1, 128).decode('utf-8')
  curses.noecho()

  command_input = command_input.split(' ')
  command = UNKNOWN_COMMAND
  args = []

  if len(command_input) > 0:
    command = command_input[0].lower()
  if command not in command_handlers:
    command = UNKNOWN_COMMAND
  if len(command_input) > 1:
    args = command_input[1:]
 
  return (command, args)


UNKNOWN_COMMAND = ''

command_handlers = {
  'follow': follow_handler,
  'unfollow': unfollow_handler,
  'followcall': follow_call_handler,
  'followput': follow_put_handler,
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

  draw_symbols(stdscr, symbols)

  while True:
    key = stdscr.getkey()
    if key == ':':
      command, args = read_command(stdscr)
      command_handlers[command](stdscr, command, args)

  stdscr.refresh()
  stdscr.getkey()

wrapper(main)
