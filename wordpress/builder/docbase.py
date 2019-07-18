import os
import subprocess 
import shutil
from urllib.parse import urlparse

class Builder:

    def __init__(self, repo_url):
        self.leet = 1337
        self.repo_url = repo_url
        self.proj_dir = self.gen_projdirs(self.repo_url)
        self.cloned = self.git_clone(self.repo_url)
        self.docs_dir = self.find_docs()
        self.is_gitbook = False
        self.is_mkdocs = True

    def gen_projdirs(self, repo_url):
        print('Generating project directory for repo + docs.')
        urlp = urlparse(repo_url).path.lstrip('/')
        print(urlp)
        docsdir = os.path.join(os.getcwd(), urlp)

        # clean all existing files; repo will be cloned into this directory
        if os.path.isdir(docsdir):
            shutil.rmtree(docsdir)

        # make the directories
        os.makedirs(docsdir, mode=0o777)
        print('Done generated project directories.')
        return docsdir

    def git_clone(self, repo_url):
        print('Cloning repo into', self.proj_dir, '.')
        try:
            docs = subprocess.run(
                ['git', 'clone', repo_url, self.proj_dir]
            )
            print(docs)
            return 'Cloned'
        except subprocess.CalledProcessError as e:
            print(e.output)
        print('Done cloning.')

    def show_docs(self):
        for root, dirs, files in os.walk(self.proj_dir):
            level = root.replace(self.proj_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print('{}{}/'.format(indent, os.path.basename(root)))
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                if f.endswith('.md') or f.endswith('.rst'):
                    print('{}{}'.format(subindent, f))

    def find_docs(self, docs_dir=None):
        if os.path.exists(os.path.join(self.proj_dir, 'SUMMARY.md')):
            self.is_gitbook = True
            print('>>> This appears to be a GitBook.')
        elif not docs_dir:
            for doc_dir_name in ['docs', 'doc', 'Doc', 'book']:
                possible_path = os.path.join(
                    self.proj_dir, 
                    doc_dir_name
                )
                if os.path.exists(possible_path):
                    docs_dir = possible_path
                    break
        if not docs_dir:
            docs_dir = self.proj_dir
        return docs_dir

#    def find_doc_builder_type(self):



#    def generate_index(self, extension='md'):
#        docs_dir = self.find_docs()
#
#        index_filename = os.path.join(
#            docs_dir,
#            'README.{ext}'.format(ext=extension),
#        )
#
#        if not os.path.exists(index_filename):
#            readme_filename = os.path.join(
#                docs_dir,
#                'README.{ext}'.format(ext=extension),
#            )
#            if os.path.exists(readme_filename):
#                return 'README'
#
#            index_file = open(index_filename, 'w+')
#            index_text = """
#            Insert a kauri welcome message here in the future
#            --------------------------------------------------
#
#            asdf
#
#            1234
#
#            asdf
#
#            1234
#
#            https://kauri.io
#            """
#            index_file.write(index_text.format(dir=docs_dir, ext=extension))
#            index_file.close()
#        return 'index'
#
#
