import arxiv
import os
import glob
from googlesearch import search
import tarfile
from scholarly import scholarly, ProxyGenerator
from functools import lru_cache
import re
import time
import random

paper_download_dir = './papers'


pg = ProxyGenerator()
pg.Tor_Internal(tor_cmd = "tor")
scholarly.use_proxy(pg)


class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


@lru_cache(None)
def get_arxiv_id(paper_title: str, feel_lucky: bool = True):
    # arxiv query by paper title is shitty
    # we use google search to get the arxiv_id
    arxiv_url = list(search(f'{paper_title} site:arxiv.org', stop=1))[0]
    arxiv_id = re.findall(r'\d+\.\d+', arxiv_url)[0]

    # papers = arxiv.query(query=paper_title)
    paper = arxiv.query(id_list=[arxiv_id])[0]
    if not feel_lucky:
        print(paper_title)
        print(paper['title'])
        if input('Should we continue') == 'n':
            return None

    # TODO assert paper_titile match paper.

    # for example http://arxiv.org/pdf/1911.05722v3 ->1911.05722v3
    return paper['pdf_url'].split('/')[-1]


def get_accurate_name_from_arxiv(paper_title: str):
    # arxiv query by paper title is shitty
    # we use google search to get the arxiv_id
    arxiv_url = list(search(f'{paper_title} site:arxiv.org', stop=1))[0]
    arxiv_id = re.findall(r'\d+\.\d+', arxiv_url)[0]

    paper = arxiv.query(id_list=[arxiv_id])[0]
    return paper['title']


@lru_cache(None)
def download_arxiv_paper(arxiv_id,
                         feel_lucky: bool = True):
    """
    Input: arxiv_id
    Return:
        the downloaded paper folder.
    """

    if not os.path.exists(paper_download_dir):
        os.makedirs(paper_download_dir)

    # Don't download again if exists
    search_this_paper = glob.glob(f'{paper_download_dir}/{arxiv_id}*/')
    if len(search_this_paper) > 0:
        return search_this_paper[0]

    tarpath = arxiv.download({'pdf_url': f"http://arxiv.org/pdf/{arxiv_id}"},
                             dirpath=paper_download_dir,
                             prefer_source_tarfile=True)
    with tarfile.open(tarpath, 'r') as tar:
        tar.extractall(
            path=tarpath.replace('.tar.gz', ''))
        return tarpath.replace('.tar.gz', '')

        # download_paper('Momentum contrast for unsupervised visual representation learning')


@lru_cache(None)
def search_paper(title: str, feel_lucky: bool=True):
    """
    Search paper through google scholar, return scholarly publication container
    """
    title = get_accurate_name_from_arxiv(title)
    pub = next(scholarly.search_pubs(title))
    if not feel_lucky:
        raise NotImplementedError
    return pub


# @lru_cache(None)
def search_cited_papers(pub):
    # only consider the most prominant ten papers.
    return [_ for _,__ in zip(scholarly.citedby(pub), range(10))]


def get_title_from_scholarly_pub(pub):
    return pub['bib']['title']


def find_within_reference(citing_paper_folder, cited_paper_title):
    try:
        bblfile = glob.glob(os.path.join(citing_paper_folder, '**/*.bbl'), recursive=True)[0] # assume only one
        # print(bblfile)
        parsed_bbl = parse_bbl(bblfile)
        bibitem = find_bibitem(cited_paper_title, parsed_bbl)
        # print(bibitem)
        if bibitem is None:
            raise Exception('No corresponding bibitem')
        texfiles = glob.glob(os.path.join(citing_paper_folder, '**/*.tex'), recursive=True)
        all_referred_places = [_ for texfile in texfiles for _ in find_in_tex(texfile, bibitem)]
        return all_referred_places
    except Exception as e:
        print(e)
        return []


def parse_bbl(bbl_file):
    """
    Take bbl_file, and return the bibitem to details.
    """
    text = open(bbl_file, 'r', errors='replace').readlines()
    text = text[1:-1]
    text = ''.join(text).strip('\n')
    text = text.split('\\bibitem')[1:]
#     print(len(text))
    d = {}
    for block in text:
        # think of case
        # \bibitem[dfdfdfd\dfefe{dsfsdfdsf}]{xxxx}
        if block.startswith('['):  # remove the [xxxx]
            block = block[block.find(']')+1:]
        alias = block[block.find('{')+1:block.find('}')]
        d[alias] = block[block.find('}')+2:].replace('\\newblock ', '').replace('{', '').replace('}', '')
        d[alias] = d[alias].replace('\n', ' ')
        d[alias] = ' '.join(d[alias].split())
    return d


def find_bibitem(paper_title, parsed_bbl):
    for k in parsed_bbl.keys():
        # 'Why can't find bibitem
        if paper_title.lower() in parsed_bbl[k].lower().replace('{', '').replace('}', ''):
            return k
    return None


def find_in_tex(texfile, bibitem):
    tex = open(texfile, 'r', errors='replace').read()
    lower_tex = tex.lower()
    # TODO
    # if '\\section{related work}' not in lower_tex:
    #     # Only find within related work for now.
    #     return
    # tex = tex[lower_tex.find('\\section{related work}')+7:]
    # tex = tex[:tex.find('\\section')]
    # preprocess
    tex = _remove_comments(tex)
    tex = ' '.join(tex.split('\n'))
    tex_lines = tex.split('.')
    for line in tex_lines:
        # if f'\\cite{{{bibitem}}}' in line:
        if bibitem in line:
            yield line.replace(bibitem, color.BOLD + bibitem + color.END) # make it bold



# copy from arxiv latex cleaner
import re
def _remove_environment(text, environment):
  """Removes '\\begin{environment}*\\end{environment}' from 'text'."""
  return re.sub(
      r'\\begin{' + environment + r'}[\s\S]*?\\end{' + environment + r'}', '',
      text)


def _remove_iffalse_block(text):
  """Removes possibly nested r'\iffalse*\fi' blocks from 'text'."""
  p = re.compile(r'\\if(\w+)|\\fi')
  level = -1
  positions_to_del = []
  start, end = 0, 0
  for m in p.finditer(text):
    if m.group() == r'\iffalse' and level == -1:
      level += 1
      start = m.start()
    elif m.group().startswith(r'\if') and level >= 0:
      level += 1
    elif m.group() == r'\fi' and level >= 0:
      if level == 0:
        end = m.end()
        positions_to_del.append((start, end))
      level -= 1
    else:
      pass

  for (start, end) in reversed(positions_to_del):
    if end < len(text) and text[end].isspace():
      end_to_del = end + 1
    else:
      end_to_del = end
    text = text[:start] + text[end_to_del:]

  return text


def _remove_comments_inline(text):
  """Removes the comments from the string 'text'."""
  if 'auto-ignore' in text:
    return text
  if text.lstrip(' ').lstrip('\t').startswith('%'):
    return ''
  match = re.search(r'(?<!\\)%', text)
  if match:
    return text[:match.end()] + '\n'
  else:
    return text


def _remove_comments(content): #, parameters):
    """Erases all LaTeX comments in the content, and writes it."""
    content = [_remove_comments_inline(line) for line in content]
    content = _remove_environment(''.join(content), 'comment')
    content = _remove_iffalse_block(content)
#     for command in parameters['commands_to_delete']:
#         content = _remove_command(content, command)
    return content