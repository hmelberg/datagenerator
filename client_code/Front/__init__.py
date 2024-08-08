from ._anvil_designer import FrontTemplate
from anvil import *
import anvil.server
import stripe.checkout
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users

from .. import Function

#from ..Options import Options
import anvil.media

from collections import Counter
import random



class Front(FrontTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    #self.column_panel_1.visible=False
    # datafile properties
    self.recipe={}
    self.n=100

    self.tied_to_column=None
    
    multiple_options=  [('only one event','one'),
                ('one or more events','multiple')] 
    self.multiple.items=multiple_options
    self.multiple.selected_value='one'
    
    self.columns={}
    # make it scrollable (if many columns)
    self.data.role = 'wide'
      
    how_options = [('a predefined pattern','predefined'),
                ('an example','example'), 
                ('a user defined pattern','user_defined'), 
                ('a regex expression','regex')] 
    
    self.how_general.items=how_options
    self.how_general.selected_value='predefined'


    rows = app_tables.patterns.search()
    self.short_name=[row['name'] for row in rows]
    self.long_name=[row['long_name'] for row in rows]
    self.pattern = [row['pattern'] for row in rows]
    self.autoid = [row['autoid'] for row in rows]
    self.headline = [row['headline'] for row in rows]
    
    self.how_specific_dropdown.items=list(zip(self.short_name, self.autoid))

    
  def ok_dataset_click(self, **event_args):
    if self.multiple.selected_value=='one':
      self.columns['id']=[str(i) for i in range(1,self.n+1)]
    else:
      events=[random.randint(0,10) for i in range(1,self.n+1)]
      self.columns['id']=[]
      for i in range(1,self.n+1):
        self.columns['id'].extend([str(i)]*events[i-1])

    self.item['headline']=Function.columns2headlines(self.columns)
    self.item['data']=Function.columns2data(self.columns)
    self.refresh_data_bindings()
    self.column_name.placeholder='col'+str(len(self.columns)+1)
    self.info_card.visible=False
    
    nrows=len(self.columns['id'])
    if self.file_name.text=='':
      file_name=self.file_name.placeholder
    else:
      file_name=self.file_name.text
      
    
    if self.multiple.selected_value=='one':
      self.file_info.text= f'{file_name} ({nrows} rows/persons)'
    else:
      nrows=len(self.columns['id'])
      self.file_info.text=f"{file_name} ({nrows} rows/events and {self.nrows.text} persons)"
      
    if self.how_general.selected_value=='predefined':
      pattern=self.how_specific_dropdown.selected_value
      suggested_name=self.headline[pattern]
      if suggested_name in self.columns:
        suggested_name=Function.suggest_column_name(suggested_name, self.columns.keys())
      self.column_name.placeholder=suggested_name

        
    last_data= [{'last column':pid} for pid in self.columns['id']]
    self.repeating_panel_2.items=last_data
    self.refresh_data_bindings()
    
    
  def generate_codes_click(self, **event_args):
    #n=len(self.columns['id'])
    n=int(self.nrows.text)
    selected = self.how_general.selected_value
         
    if selected=='example':
      pattern=self.how_specific_text.text
      if pattern=='':
        pattern=self.how_specific_text.placeholder
      codes=Function.random_code_from_simple_pattern(pattern=pattern, n=n)
    elif selected=='predefined':
      pattern=self.how_specific_dropdown.selected_value
      pattern=self.pattern[pattern]
      if pattern.startswith('['):
        codes=Function.random_code_from_recipe(pattern=pattern, n=n)
      else:
        codes=Function.random_code_from_simple_pattern(pattern=pattern, n=n) 
    elif selected=='user_defined':
      pattern=self.how_specific_text.text
      if pattern=='':
        pattern=self.how_specific_text.placeholder
      codes=Function.random_code_from_recipe(pattern=pattern, n=n)
    elif 'list' in selected:
      codes=Function.random_code_from_list(selected, n=n)
    elif selected == 'regex':
      pattern=self.how_specific_text.text
      if pattern=='':
        pattern=self.how_specific_text.placeholder
      codes=anvil.server.call('from_regex',pattern, n=n)
    
    # could be more efficient (use list multiplication?)
    if self.tied_to_column:
      key=self.tied_to_column
      old_col=self.columns[self.tied_to_column]
      col_unique=set(old_col)
      
      old2new={}
      for i, value in enumerate(col_unique):
        old2new[value]=codes[i]
      codes=[old2new[old] for old in old_col]
    else:
      key=None
      
    if self.column_name.text=='':
      name=self.column_name.placeholder
      self.columns[name]=codes
      n=len(self.columns)
      self.column_name.placeholder='col_'+str(n+1)
    else:
      name=self.column_name.text
      self.columns[name]=codes
      n=len(self.columns)
      self.column_name.placeholder='col_'+str(n+1)
    
    if selected=='predefined':     
      pattern=self.how_specific_dropdown.selected_value
      suggested_name=self.headline[pattern]
      if suggested_name in self.columns:
        suggested_name=Function.suggest_column_name(suggested_name, self.columns.keys())
      self.column_name.placeholder=suggested_name
   
    self.update_data() 
    
    # keep a record of the recipe for how the columns were made
    record = {'column':name, 'base':selected, 'pattern':pattern, 'key':key}
    self.recipe.update(record)
    
    last_data= [{name:code} for code in codes]
    self.repeating_panel_2.items=last_data
    self.refresh_data_bindings()
       
    return 
    
  def update_data(self, **event_args):
    self.item['headline']=Function.columns2headlines(self.columns)
    self.item['data']=Function.columns2data(self.columns)

    self.refresh_data_bindings()
    last_headline=self.data.columns[-1]
    self.last_column.columns=[last_headline]
    
    #todo (update last column too)
    #last_data= [{name:code} for code in codes]
    #self.repeating_panel_2.items=last_data
    #self.refresh_data_bindings()

  def download_click(self, **event_args):
    headline=[str(name) for name in self.columns.keys()]
    headline_string=';'.join(headline)+'\n'
    
    data=zip(*self.columns.values())
    data=[';'.join(row) for row in list(data)]
    data_string='\n'.join(data)
    
    data_csv=headline_string+data_string
    data_csv = data_csv.encode('utf8')
    #print(data_csv)
    
    codes_media = anvil.BlobMedia('text/plain',data_csv)
    anvil.media.download(codes_media) 
    


  
  def add_demographics_click(self, **event_args):
      n=int(self.nrows.text)
      
      age = [random.randint(0,105) for i in range(n)]
      places = ['north', 'south', 'east', 'west']
      location = [random.choice(places) for i in range(n)]
      
      current_output = self.code_output.tag.codes
      
      if self.code_output.tag.codes=='':
        all_output = [str(i)+';'+str(age[i])+';'+location[i] for i in range(n)]
      else:
        current_output = current_output.splitlines()
        all_output = [str(i)+';'+str(age[i])+';'+location[i]+';'+current_output[i] for i in range(n)]

      self.code_output.tag.headline.extend(['person_id', 'age', 'region'])
      
      self.code_output.text=Function.format_output(all_output[:10], self.code_output.tag.headline)
      all_output = '\n'.join(all_output)
      self.code_output.tag.codes=all_output
      



    

  def save_and_share_click(self, **event_args):
    filename = TextBox(placeholder="Filename")
    result = alert(content=filename,
               title="Enter filename",
               large=True,
               buttons=[
                 ("Cancel", "Cancel"),
                 ("OK", "OK")
               ])
    if result=='Cancel':
      return
    csv=self.code_output.tag.codes
    folder = app_files.csv
    #todo: check if filename exist already?
    new_file = folder.create_file(filename.text, csv)
    file_id = new_file.id
    url = f'https://drive.google.com/open?id={file_id}'
    
    url_text = TextBox(text=url)
    result = alert(content=url_text,
               title="Copy link to clipboard?",
               large=True,
               buttons=[
                 ("Cancel", "Cancel"),
                 ("OK", "OK")
               ])
    if result=='Cancel':
      return
    self.output_url.text = url_text.text
    self.call_js("copyclip", self.output_url.text)
      
    return url

  def get_link_to_share_click(self, **event_args):
    filename = TextBox(placeholder="Filename")
    result = alert(content=filename,
               title="Enter filename",
               large=True,
               buttons=[
                 ("Cancel", "Cancel"),
                 ("OK", "OK")
               ])
    if result=='Cancel':
      return
    csv=self.code_output.tag.codes
    folder = app_files.csv
    #todo: check if filename exist already?
    new_file = folder.create_file(filename.text, csv)
    file_id = new_file.id
    url = f'https://drive.google.com/open?id={file_id}'
    
    url_text = TextBox(text=url)
    result = alert(content=url_text,
               title="Copy link to clipboard?",
               large=True,
               buttons=[
                 ("Cancel", "Cancel"),
                 ("OK", "OK")
               ])
    if result=='Cancel':
      return
    self.output_url.text = url_text.text
    #print(url_text.text)
    self.call_js("copyclip", self.output_url.text)
      

  def how_dropdown_change(self, **event_args):
    if (self.how_general.selected_value=='user_defined'):
      self.how_specific_dropdown.visible=False
      self.how_specific_text.placeholder='[A,B][x,y,z;p=(0.8,0.1,0.1)][1-3][.][0-9]'
      self.how_specific_text.visible=True
      #self.save_pattern.visible=True
      
    elif (self.how_general.selected_value=='example'):
      self.how_specific_dropdown.visible=False
      self.how_specific_text.placeholder='K50.1'
      self.how_specific_text.visible=True
      #self.search_pattern.visible=False
      #self.save_pattern.visible=True
    elif (self.how_general.selected_value=='regex'):
      self.how_specific_dropdown.visible=False
      self.how_specific_text.placeholder=r'[A-Z]\d[A-Z] \d[A-Z]\d''
      self.how_specific_text.visible=True
      #self.search_pattern.visible=False
      #self.save_pattern.visible=True
    else:
      self.how_specific_dropdown.visible=True
      self.how_specific_text.visible=False
      #self.save_pattern.visible=False
      #self.search_pattern.visible=True
    
    existing=True
    i=0
    while existing is True:
      i=i+1
      suggested_column_name='col_'+str(len(self.columns)+i)
      if suggested_column_name not in self.columns:
        existing=False
        
    if self.how_general.selected_value=='predefined':
      suggested_column_name=self.headline[self.how_specific_dropdown.selected_value]
      if suggested_column_name in self.columns:
        suggested_column_name=Function.suggest_column_name(suggested_column_name, self.columns.keys())
    self.column_name.placeholder=suggested_column_name

  def how_specific_dropdown_change(self, **event_args):
    pattern=self.how_specific_dropdown.selected_value
    suggested_name=self.headline[pattern]
    if suggested_name in self.columns:
      suggested_name=Function.suggest_column_name(suggested_name, self.columns.keys())
    self.column_name.placeholder=suggested_name
    

  def tie_to_bool_clicked(self, **event_args):
    self.tie_to_column.items=self.columns.keys()


  def about_click(self, **event_args):
    self.about_panel.visible=True
    self.front_panel.visible=False
    self.home.visible=True
    self.about.visible=False
  
  def home_click(self, **event_args):
    self.about_panel.visible=False
    self.front_panel.visible=True
    self.home.visible=False
    self.about.visible=True

  def delete_column_click(self, **event_args):
    columns=self.columns.keys()
    del_col_dd=DropDown(items=columns)
    result=alert(content=del_col_dd, title='Select column to be deleted',buttons=[('Delete', 'delete'), ('Cancel', 'cancel')])
    if result=='delete':
      del self.columns[del_col_dd.selected_value]
      self.update_data()
      #todo: deal with number problems? atc_1 etc

  def tie_data_btn_click(self, **event_args):
    if self.tied_to_column is None:
      columns=self.columns.keys()
      tied_to_column_dd=DropDown(items=columns)
      result=alert(content=tied_to_column_dd, 
                   title='Column for which the new values should be stable',
                   buttons=[('Cancel', 'cancel'),('Select', 'select')])
      if result=='select':
        self.tied_to_column=tied_to_column_dd.selected_value
        self.tie_data_btn.text=f'END KEY BINDING'
        self.tie_data_btn.tooltip=f"Click to untie. Currently new values are related to {self.tied_to_column}"
    else:
        self.tied_to_column=None
        self.tie_data_btn.text='Tie new data to key'
        self.tie_data_btn.tooltip=f"Example: Birth year should be constant for the same person in the data (id as key)"
      
    
    
      
    

  def button_4_copy_click(self, **event_args):
    """This method is called when the button is clicked"""
    pass

  def save_pattern_click(self, **event_args):
    user=anvil.users.get_user()
    if not user:
      Notification(message='You must be a registred user to save patterns')
    else:
      content=ColumnPanel()
      
      short_name=TextBox(placeholder='Short name of pattern (eg. ICD-10)')
      long_name=TextBox(placeholder='Long name of pattern (International ...)')
      headline=TextBox(placeholder='Suggested variable name (eg. date_of_birth)')
      tags = TextBox(placeholder='Tags relevant to this pattern (e.g. icd9, 2012, USA)')
      link = TextBox(placeholder='Link to further information')

      components = [short_name, long_name, headline, tags, link]
      for component in components:
        content.add_component(component)
      
      result=alert(title='Save the current pattern', content=content, large=True, buttons=['Cancel','Save'])
      if result=='Save':
        app_tables.patterns.query()
        rows=app_tables.patterns.search()[-1]
        autoid=rows['autoid']+1
        app_tables.patterns.add_row(name=short_name.text,
                                  pattern=self.how_specific_text.text,
                                  created_by=user['email'],
                                   link=link.text,
                                   long_name=long_name.text,
                                   headline=headline.text,
                                   tags=tags.text,
                                   autoid=autoid)
      
      #todo:add exitence checks and more info (date, email?, check if registered?)

  def save_data_click(self, **event_args):
    user=anvil.users.get_user()
    if not user:
      Notification(message='You must be a registred user to save patterns')
    else:
      content=ColumnPanel()
      
      short_name=TextBox(placeholder='Short name of pattern (eg. ICD-10)')
      long_name=TextBox(placeholder='Long name of pattern (International ...)')
      headline=TextBox(placeholder='Suggested variable name (eg. date_of_birth)')
      tags = TextBox(placeholder='Tags relevant to this pattern (e.g. icd9, 2012, USA)')
      link = TextBox(placeholder='Link to further information')

      components = [short_name, long_name, headline, tags, link]
      for component in components:
        content.add_component(component)
      
      result=alert(title='Save the current pattern', content=content, large=True, buttons=['Cancel','Save'])
      if result=='Save':
        app_tables.patterns.query()
        rows=app_tables.patterns.search()[-1]
        autoid=rows['autoid']+1
        app_tables.patterns.add_row(name=short_name.text,
                                  pattern=self.how_specific_text.text,
                                  created_by=user['email'],
                                   link=link.text,
                                   long_name=long_name.text,
                                   headline=headline.text,
                                   tags=tags.text,
                                   autoid=autoid)
      

  def search_data_click(self, **event_args):
    open_form('Front.Browse')
    

  def column_name_pressed_enter(self, **event_args):
    """This method is called when the user presses Enter in this text box"""
    pass

  def new_file_click(self, **event_args):
    self.columns={}
    self.info_card.visible=True
    self.step_1_headline.visible=True
        # datafile properties
    self.file_name.placeholder='name'
    self.n=100

    self.tied_to_column=None
    
    #self.multiple.selected_value='one'
    
    self.item['headline']=None
    self.item['data']=None
    self.recipe={}
    
    self.column_name.placeholder='col_1'
    self.repeating_panel_2.items=[]
    self.last_column.columns=[]
    self.data.columns=[]
    #self.data.clear()
    #self.last_column.clear()
    self.repeating_panel_1.items=[]
    self.refresh_data_bindings()
    
    













































 
#def button_1_click(self, **event_args):
#  self.call_js("copyclip", self.lbl_odscode.text)

#https://drive.google.com/open?id=1tsr5-EM68JshRRtl5QGbfLPoZEZLfMe9

#17QU8ZQ0RPZgzO_S6kKYdhuST0l1QV_Wx
#"https://tinyurl.com/create.php" method="post" target="_blank"
#https://drive.google.com/open?id=17QU8ZQ0RPZgzO_S6kKYdhuST0l1QV_Wx


#https://tinyurl.com/create.php?method=post?target=https://drive.google.com/open?id=17QU8ZQ0RPZgzO_S6kKYdhuST0l1QV_Wx

#https://tinyurl.com/create.php?source=create&url=https%3A%2F%2Fdrive.google.com%2Fopen%3Fid%3D17QU8ZQ0RPZgzO_S6kKYdhuST0l1QV_Wx&alias=

#https://tinyurl.com/create.php?source=create&url=https%3A%2F%2Fdrive.google.com%2Fopen%3Fid%1tsr5-EM68JshRRtl5QGbfLPoZEZLfMe9&alias=

#https://tinyurl.com/create.php?source=create&url=https%3A%2F%2Fdrive.google.com%2Fopen%3Fid%3D17QU8ZQ0RPZgzO_S6kKYdhuST0l1QV_Wx&alias=hospital_ibd

#https://api-ssl.bitly.com/v4/shorten?group_guid:string?domain=bit.ly?long_url=https%3A%2F%2Fdrive.google.com%2Fopen%3Fid%1tsr5-EM68JshRRtl5QGbfLPoZEZLfMe9
#  
#  "group_guid": "string",
#"domain": "bit.ly",
#"long_url": "string"

#https://cloud.google.com/storage/pricing#price-tables
#https://www.digitalocean.com/docs/spaces/
#https://www.digitalocean.com/community/questions/how-to-upload-an-object-to-digital-ocean-spaces-using-python-boto3-library
#https://medium.com/@tatianatylosky/uploading-files-with-python-using-digital-ocean-spaces-58c9a57eb05b
#https://github.com/smartfile/client-python/
#https://help.github.com/en/github/working-with-github-pages/configuring-a-custom-domain-for-your-github-pages-site
#https://cognitiveclass.ai/blog/read-and-write-csv-files-in-python-from-cloud
#https://github.com/PyGithub/PyGithub
#Or Google "sync github with google drive"
#https://zapier.com/apps/github/integrations/google-drive





 
  
