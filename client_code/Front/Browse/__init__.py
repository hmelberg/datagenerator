from ._anvil_designer import BrowseTemplate
from anvil import *
import anvil.server
import stripe.checkout
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

class Browse(BrowseTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.repeating_panel_1.items=app_tables.csv.search()
    
    # Any code you write here will run when the form opens.

  def button_1_click(self, **event_args):
    self.repeating_panel_1.items=app_tables.csv.search()
