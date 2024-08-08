import anvil.server
import stripe.checkout
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server


from collections import Counter
import random



def random_choice(options, p, noptions):
  a = True
 
  while a:
    suggested_option_num = random.randint(0,noptions-1)
    rnd_num = random.uniform(0,1)
    if rnd_num<p[suggested_option_num]:
      a=False
  return options[suggested_option_num]

def random_choices(options, p=None, n=1):
  noptions=len(options)
  if p is None:
    p=[1/noptions]*noptions    
  random_codes = [random_choice(options=options, p=p, noptions=noptions) for i in range(n)]
  return random_codes
#%%
  
def random_code_from_simple_pattern(pattern, numbers=None, letters=None, n=1):
  codes=['']*n
  if letters is None:
    letters = list('abcdefghijklmnopqrstuwxyz')
  if numbers is None:
    numbers = [str(num) for num in range(10)]
  
  for step, symbol in enumerate(list(pattern)):
    if symbol.isnumeric():
      random_symbol = random_choices(numbers, n=n)
      random_symbol = [str(num) for num in random_symbol]

    elif symbol.isalpha():
      if symbol.isupper():
        random_symbol = random_choices(letters, n=n)
        random_symbol=[symbol.upper() for symbol in random_symbol]
      else:
        random_symbol = random_choices(letters, n=n)
        
    else:
      random_symbol=[symbol]*n
    codes = list(zip(codes, random_symbol))
    codes = [''.join(code) for code in codes]
    #if len(codes)==1:
    #  codes=codes[0]
  return codes

#%%


#%%
def random_code_from_recipe(pattern, n=1):
  """
  pattern='[a-f][1-3][x,y]'
  pattern='[a-f][.,''][1-3][x,y]'
  pattern='[a-f][,;p=(0.5)][1-3][x,y]'
  pattern='[a-f][1-3][x,y][.][1-8]'
  pattern='[a-f,1-3][1-3][x,y][.][1-8]'
  pattern='[a-f][1-3][x,y;p=(0.1, 0.9)][.][1-8]'
  random_code_from_recipe(pattern=pattern, n=10)
  """
  exprs = pattern.split(']')
  exprs = [interval.strip('[') for interval in exprs[:-1]]
  
  codes=['']*n
  
  for step, expr in enumerate(exprs):
    hyphen = '-' in expr
    comma = ',' in expr
    longer_than_two = len(expr)>2
    
    if hyphen & longer_than_two & (not comma):
      if ';p=' in expr:
        expr, p = expr.split(';')
        start, end = expr.split('-')
        start_num = ord(start)
        end_num = ord(end)
        
        options = [chr(num) for num in range(start_num, end_num)]
        noptions=len(options)
        options.append('')
        
        p=p.split('(')[1].strip(')')
        p=noptions*[float(p)/noptions]
        p.append(1-sum(p))
        random_symbol = random_choices(options, p=p, n=n)
      else:
        #print(expr)
        start, end = expr.split('-')
        start_num = ord(start)
        end_num = ord(end)
        # only works with standard english characters, todo warn if not
        #todo:check if end is inclusive or exclusive, may need to add one, yes think so, but check
        random_int =  [random.randint(start_num, end_num) for num in range(n)]
        random_symbol=[chr(num) for num in random_int]
    elif comma & longer_than_two & (not hyphen):
        if ';p=' in expr:
          expr, p = expr.split(';')
          options = expr.split(',')
          #todo: allow comma and hyphen to be symbols (if escaped?)
          p=p.split('(')[1].strip(')').split(',')
          p=[float(pr) for pr in p]
          if sum(p)<1:
            options.append('')
            p.append(1-sum(p))
          noptions=len(options)
          random_symbol = random_choices(options, p=p, n=n)
        else:
          options = expr.split(',')
          #todo: allow comma and hyphen to be symbols (if escaped?)
          noptions=len(options)
          p = noptions * [1/noptions]
          random_symbol = random_choices(options, p=p, n=n)
    
    #  pattern='[a-f,1-3][1-3][x,y][.][1-8]'
    elif comma & longer_than_two & hyphen:
        if ';p=' in expr:
          expr, p = expr.split(';')
          options = expr.split(',')
          p=p.split('(')[1].strip(')').split(',')
          p=[float(pr) for pr in p]
          if sum(p)<1:
            options.append('')
            p.append(1-sum(p))
        else:
          options = expr.split(',')
          #todo: allow comma and hyphen to be symbols (if escaped?)
          noptions=len(options)
          p = noptions * [1/noptions]
        unexpanded_options = options
        expanded_options = []
        expanded_p = []
        
        for option_num, option in enumerate(unexpanded_options):
          start, end = option.split('-')
          start_num = ord(start)
          end_num = ord(end)
          possible_symbols=[chr(num) for num in range(start_num,end_num+1)]
          expanded_options.extend(possible_symbols)
          n_possible = len(possible_symbols)
          old_p = p[option_num]
          expanded_p.extend(n_possible * [old_p/n_possible])
        random_symbol = random_choices(expanded_options, p=expanded_p, n=n)       
      
    else:
      random_symbol=[expr]*n

    codes = list(zip(codes, random_symbol))
    codes = [''.join(symbols) for symbols in codes]

  if len(codes)==1:
    codes=codes[0]
  return codes

def random_code_from_list(name, n=1):
  codes = [r['icd10list'] for r in app_tables.codes.search()]
  codes = random_choices(codes, n=n)
  return codes


def get_code_type(codes):
  kwarg={}
  if codes=='ATC':
    kwarg['pattern'] = 'A01AA01'
    kwarg['letters'] = list('abcdghjlmnprsv'.upper())
    kwarg['numbers'] = [str(num) for num in range(10)]

  elif codes =='ICD-10 International':
    kwarg['pattern'] = 'K50.1'
    kwarg['letters'] = list('abcdefghigjklmnopqrstuvwxyz'.upper())
    kwarg['numbers'] = [str(num) for num in range(10)]
  return kwarg

def format_output(text, headline):
  new_text=''
  headline = ';'.join(headline)
  text.insert(0, headline)
  for line in text:
    words = line.split(';')
    spaced_words = [str(word).ljust(10, ' ') for word in words]
    new_line = ''.join(spaced_words)
    new_text = new_text+'\n'+new_line
  
  return new_text
    
def format_output_markdown(text, headline):
  new_text=''
  headline = '|'.join(headline)
  text.insert(0, headline)
  for line in text:
    words = line.split(';')
    spaced_words = [str(word).ljust(10, ' ') for word in words]
    new_line = ''.join(spaced_words)
    new_text = new_text+'\n'+new_line
  
  return new_text

def columns2data(columns):
  cols=columns.keys()
  #n=len(columns[cols[0]])
  n=int(self.nrows.text)
  #print(n)
  data = [{col:columns[col][i] for col in cols} for i in range(n)] 
  return data


def columns2headlines(columns):
  cols=columns.keys()
  headline= [{'id':col, 'title':col, 'data_key':col, 'expand':True} for col in cols] 
  for i,col in enumerate(cols):
    col_length=len(col)
    content_length=len(str(columns[col][0]))
    length=max(col_length, content_length)
    width=10*length
    headline[i]['width']=width
  return headline

def suggest_column_name(suggested_name, column_names):
  clean_names=[col.split('_',1)[0] for col in column_names]
  count=Counter(clean_names)
  #if count[suggested_name]==1:
  #  suggested = suggested_name+'_1'
  #else:
  n=count[suggested_name]
  suggested = suggested_name+'_'+str(n)
  return suggested
     
