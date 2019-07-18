import os 
import yaml 
import json
import pprint

#from docs.builder.docbase import Builder

class MkDocsBuilder():
    """
    MkDocs -> Kauri Docs Builder
    This is more of a parser than a builder. Nothing is being generated.
    """


    def __init__(self, proj_dir, docs_dir, repo_url):
        self.proj_dir = proj_dir
        self.docs_dir = docs_dir
        self.repo_url = repo_url
        self.yaml_file = self.get_yaml_file()
        self.loaded_yaml_file = self.load_yaml_file()
        self.md_source = self.create_kauri_docs_layout()

    def get_yaml_file(self, mkdoc_path=None):
        if not mkdoc_path:
            mkdoc_path = os.path.join(
                self.proj_dir, 
                'mkdocs.yml'
            )
            if not os.path.exists(mkdoc_path):
                print('YAML file not found')
                return None
        return mkdoc_path

    def load_yaml_file(self):
        try:
            # TODO: remember, write code to close this yaml file
            return yaml.safe_load(open(self.yaml_file, 'r'),)
        except IOError:
            # if file empty, write repo_url
            return {
                'repo_url' : self.repo_url,
            }

    def _nav_recursion(self, dicts):
        # TODO: recursion is overwriting these values, needs to be fixed
        index_ct = 0
        result = []

        for d in dicts:
            ((k, v),) = d.items()

            if isinstance(v, list):
                self._nav_recursion(v)
            else:
                src_dir = os.path.join(self.docs_dir, str(v))
                with open(src_dir, 'r') as f:
                    source = f.read()
                    f.close()

                article = {
                    'index':    index_ct,
                    'title':    k,
                    'filename': v,
                    'latest_commit': 'TBU', #TODO: set later
                    'updated': 'True/False',
                    'source':  source, # md string of article, not incl. for demo
                }
                result.append(article)
                index_ct += 1

        return result

    def create_kauri_docs_layout(self):
        mkdocs_yaml     = self.loaded_yaml_file
        pages_subdict   = mkdocs_yaml['pages']

        result          = self._nav_recursion(pages_subdict)
        
        kauri_collection = {
            'docs_name':    mkdocs_yaml['site_name'],   # collection name 
            'docs_type':    'mkdocs',                   # set mkdocs as docs type
            'origin_url':   mkdocs_yaml['site_url'],    # e.g. importer origin url
            'author':       mkdocs_yaml['site_author'], # need auth b/w GH / JWT
            'repo_url':     mkdocs_yaml['repo_url'],    # repo url, may not be needed...
            'kauri_nav':    result,                     # the markdown pages in array
        }

        pprint.pprint(kauri_collection)
        return kauri_collection

