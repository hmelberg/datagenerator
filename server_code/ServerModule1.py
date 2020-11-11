import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import rstr


@anvil.server.callable
def from_regex(expr, n):
  codes=[rstr.xeger(expr) for n in range(n)]
  return codes



