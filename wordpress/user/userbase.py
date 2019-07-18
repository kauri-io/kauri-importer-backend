import os
import subprocess

class Community:
    def __init__(self, repo_url):
        self._repo_url = repo_url
        
    @property
    def repo_url(self):
        print('Retrieving repository URL.')
        return self._repo_url

    @repo_url.setter
    def set_repo(self, repo_url):
        self._repo_url = repo_url
    
    # some thoughts:
    # 1) should we retrieve project or community github information here? 

