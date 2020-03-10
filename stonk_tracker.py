from enum import Enum
from threading import Thread, Event
from datetime import datetime

import pandas as pd
import yfinance as yf

import curses
from curses import wrapper

class Symbol:
  def __init__(self, name):
    self.name = name
    self.price = -1
    self.previous_close = -1

  def __eq__(self, other):
    if isinstance(other, Symbol):
      return self.name == other.name
    elif isinstance(other, str):
      return self.name == other
    return False

  def __str__(self):
    return '{}: {}'.format(self.name, type(self))

  @property 
  def percent_change(self):
    # Double check we're not crashing here
    if self.previous_close != 0:
      return (self.price / self.previous_close - 1) * 100
    return 0

class Stock(Symbol):
  def __init__(self, name):
    super().__init__(name)

class Option(Symbol):
  def __init__(self, name, expiry_date, strike_price, option_type):
    super().__init__(name)
    self.expiry_date = expiry_date
    self.strike_price = float(strike_price)
    self.type = option_type

class OptionType(Enum):
  UNKNOWN = 0
  CALL = 1
  PUT = 2

class TriggerableTimer(Thread):
  def __init__(self, callback):
    super().__init__()
    self._callback = callback
    self._triggered = Event()
    self._stopped = False

  def trigger(self):
    self._triggered.set()

  def stop(self):
    self._stopped
    self._triggered.set()

  def run(self):
    while True:
      self._triggered.wait(60)
      # Check if we're done
      if self._stopped:
        log('timer stopped')
        break
      log('timer triggered')
      self._callback()
      self._triggered.clear()

def val(pd_object):
  return pd_object.values[0]

################################################################################
# Logging
################################################################################

def get_current_timestamp():
  return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log(s):
  max_row, _ = stdscr.getmaxyx()
  stdscr.addstr(max_row-2, 0, '{}> {}'.format(get_current_timestamp(), s), curses.color_pair(0))
  stdscr.clrtoeol()
  stdscr.refresh()

def warn(s):
  max_row, _ = stdscr.getmaxyx()
  stdscr.addstr(max_row-2, 0, '{}> {}'.format(get_current_timestamp(), s), curses.color_pair(3))
  stdscr.clrtoeol()
  stdscr.refresh()

def error(s):
  max_row, _ = stdscr.getmaxyx()
  stdscr.addstr(max_row-2, 0, '{}> {}'.format(get_current_timestamp(), s), curses.color_pair(2))
  stdscr.clrtoeol()
  stdscr.refresh()

################################################################################
# Web calls
################################################################################

def refresh_stock(stock):
  log('refreshing data for stock {}'.format(stock.name))

  yft_info = yf.Ticker(stock.name).info
  stock.price = (yft_info['bid'] + yft_info['ask'])/2
  stock.previous_close = yft_info['regularMarketPreviousClose']

def refresh_option(option):
  log('refreshing data for option {}'.format(option.name))

  yft_option_chain = yf.Ticker(option.name).option_chain(option.expiry_date)
  if option.type == OptionType.CALL:
    yft_options = yft_option_chain.calls
  elif option.type == OptionType.PUT:
    yft_options = yft_option_chain.puts
  yft_option = yft_options[yft_options['strike'] == option.strike_price]

  option.price = val((yft_option['bid'] + yft_option['ask'])/2)
  option.previous_close = option.previous_close + 1

def refresh_symbol(symbol):
  if isinstance(symbol, Stock):
    refresh_stock(symbol)
  elif isinstance(symbol, Option):
    refresh_option(symbol)
  else:
    error('Unknown symbol {}'.format(symbol))

def refresh_symbols(symbols):
  log('refreshing all symbols...')
  for symbol in symbols:
    try:
      refresh_symbol(symbol)
    except Exception:
      error('failed to refresh {}'.format(symbol.name))
  log('refreshed all symbols!')

def refresh_thread_callback():
  refresh_symbols(symbols)
  draw_symbols(stdscr, symbols)

################################################################################
# Drawing Functions
################################################################################

def draw_symbol(stdscr, row, symbol):
  stdscr.addstr(row, 0, symbol.name)
  stdscr.addstr(row, 20, '{:.2f}'.format(symbol.price))

  if symbol.percent_change > 0:
    percent_color = curses.color_pair(1)
  elif symbol.percent_change < 0:
    percent_color = curses.color_pair(2)
  else:
    percent_color = curses.color_pair(0)
  stdscr.addstr(row, 30, '{:.2f}%'.format(symbol.percent_change), percent_color)
  stdscr.clrtoeol()

def draw_symbols(stdscr, symbols):
  for i, symbol in enumerate(symbols):
    draw_symbol(stdscr, i, symbol)
  stdscr.refresh()

def redraw_screen(stdscr, symbols):
  stdscr.clear()
  draw_symbols(stdscr, symbols)
  log('redrew screen')

################################################################################
# Command Handlers
################################################################################

def follow_handler(stdscr, command, args):
  stock = Stock(args[0])
  log('adding stock {}'.format(stock))
  try:
    refresh_stock(stock)
    symbols.append(stock)
    draw_symbols(stdscr, symbols)
    log('added {}'.format(stock))
  except Exception:
    error('failed to add stock {}'.format(stock))

def unfollow_handler(stdscr, command, args):
  try:
    symbols.remove(args[0])
    draw_symbols(stdscr, symbols)
    log('unfollowed {}'.format(args[0]))
  except Exception:
    error('couldn\'t unfollow {}'.format(args[0]))

def follow_call_handler(stdscr, command, args):
  # followoption SPY 2020-03-08
  option = Option(args[0], args[1], args[2], OptionType.CALL)
  log('adding call {}'.format(option))
  try:
    refresh_option(option)
    symbols.append(option)
    draw_symbols(stdscr, symbols)
    log('added {}'.format(option))
  except Exception:
    error('failed to add option {}'.format(option))

def follow_put_handler(stdscr, command, args):
  # followoption SPY 2020-03-08
  option = Option(args[0], args[1], args[2], OptionType.PUT)
  log('adding put {}'.format(option))
  try:
    refresh_option(option)
    symbols.append(option)
    draw_symbols(stdscr, symbols)
    log('added {}'.format(option))
  except Exception:
    error('failed to add put {}'.format(option))

def refresh_handler(stdscr, command, args):
  refresh_thread.trigger()

def exit_handler(stdscr, command, args):
  exit()

def unknown_command_handler(stdscr, command, args):
  stdscr.addstr(6, 0, 'unknown command')

def read_command(stdscr):
  max_row, _ = stdscr.getmaxyx()
  # Draw at the bottom
  stdscr.addstr(max_row-1, 0, ':')
  stdscr.clrtoeol()
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
  'followcall': follow_call_handler,
  'followput': follow_put_handler,
  'unfollow': unfollow_handler,
  'refresh': refresh_handler,
  'exit': exit_handler,
  '': unknown_command_handler,
}

schd = Stock('SCHD')
schd.price = 50.1
schd.previous_close = 52

ivv = Stock('IVV')
ivv.price = 201.5
ivv.previous_close = 190

spy = Stock('SPY')
spy.price = 291.5
spy.previous_close = 291.5

symbols = [schd, ivv, spy]

def main(ss):
  global stdscr
  stdscr = ss

  stdscr.clear()

  curses.use_default_colors()
  curses.init_pair(1, curses.COLOR_GREEN, -1)
  curses.init_pair(2, curses.COLOR_RED, -1)
  curses.init_pair(3, curses.COLOR_YELLOW, -1)

  draw_symbols(stdscr, symbols)

  # start refreshing
  global refresh_thread
  refresh_thread = TriggerableTimer(refresh_thread_callback)
  refresh_thread.start()

  while True:
    key = stdscr.getkey()
    if key == ':':
      command, args = read_command(stdscr)
      command_handlers[command](stdscr, command, args)
    elif key == 'KEY_RESIZE':
      redraw_screen(stdscr, symbols)

  stdscr.refresh()
  stdscr.getkey()

wrapper(main)
